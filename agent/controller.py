import json

from anomaly_detector import detect_anomalies
from tool_reasoner import build_investigate_agent, build_verify_agent
from pure_reasoner import build_hypothesize_agent, build_brief_agent
from runner_helpers import run_agent_with_tool_calls
from evidence import new_evidence_entry, HypothesisSet, Brief, validate_brief


def _strip_detail(anomaly: dict) -> dict:
    return {k: v for k, v in anomaly.items() if k != "hourly_detail"}


class InvestigationController:
    def __init__(self, run_query, title_id: str, on_event=None):
        """
        run_query: callable(sql: str) -> list[dict], from db_adapters.py --
            used ONLY for the deterministic OBSERVE step, never for agent calls.
        title_id: the title under investigation.
        on_event: optional callback(step: str, payload: dict), for a future
            UI/SSE layer to hook into. Safe to leave as None for now.
        """
        self.run_query = run_query
        self.title_id = title_id
        self.evidence_log = []
        self.on_event = on_event or (lambda step, payload: None)

    def _emit(self, step, payload):
        self.on_event(step, payload)


    def observe(self) -> list[dict]:
        self._emit("OBSERVE", {"status": "running"})
        anomalies = detect_anomalies(self.run_query, self.title_id)

        for a in anomalies:
            is_completion = "completion" in a["anomaly_type"]
            baseline_val = (
                a["baseline_range"]["p50_completion_pct"] if is_completion
                else a["baseline_range"]["p50_views_per_hour"]
            )
            new_evidence_entry(
                self.evidence_log, "observed_fact", "OBSERVE",
                claim_text=(
                    f"{a['region']} showed a {a['anomaly_type']} between hours "
                    f"{a['window_start_hour']}-{a['window_end_hour']} "
                    f"(observed={a['observed_value']}, baseline={baseline_val})"
                ),
                sql=None,  
                result_sample=a,
            )
            
            a["_evidence_id"] = self.evidence_log[-1]["id"]

        self._emit("OBSERVE", {"status": "done", "anomaly_count": len(anomalies)})
        return anomalies

    def investigate(self, anomaly: dict) -> list[str]:
        self._emit("INVESTIGATE", {"status": "running", "anomaly_id": anomaly["anomaly_id"]})
        agent = build_investigate_agent()
        prompt = (
            "Here is a confirmed anomaly, detected deterministically (not by you):\n\n"
            f"{json.dumps(_strip_detail(anomaly), indent=2)}\n\n"
            f"Investigate why this happened. The title_id is '{self.title_id}'."
        )
        _, tool_calls = run_agent_with_tool_calls(agent, prompt)

        new_ids = []
        for call in tool_calls:
            if call["tool_name"] not in ("run_query", "run_chdb_select_query"):
                continue
            sql = call["args"].get("query", str(call["args"]))
            entry = new_evidence_entry(
                self.evidence_log, "observed_fact", "INVESTIGATE",
                claim_text=f"Investigation query result for anomaly {anomaly['anomaly_id']}",
                sql=sql,
                result_sample=call["response"],
            )
            new_ids.append(entry["id"])

        self._emit("INVESTIGATE", {"status": "done", "evidence_ids": new_ids})
        return new_ids



    def hypothesize(self, anomaly: dict, evidence_ids: list[str]) -> list[dict]:
        self._emit("HYPOTHESIZE", {"status": "running"})
        agent = build_hypothesize_agent()
        relevant = [e for e in self.evidence_log if e["id"] in evidence_ids]
        prompt = (
            f"Anomaly:\n{json.dumps(_strip_detail(anomaly), indent=2)}\n\n"
            f"Evidence gathered during investigation:\n{json.dumps(relevant, indent=2, default=str)}\n\n"
            "Propose 2-3 hypotheses for this anomaly. Cite ONLY the evidence ids given above."
        )
        text, _ = run_agent_with_tool_calls(agent, prompt)
        hset = HypothesisSet.model_validate_json(text)

        hyps = []
        for h in hset.hypotheses:
            entry = new_evidence_entry(
                self.evidence_log, "hypothesis", "HYPOTHESIZE",
                claim_text=h.text,
                supports=h.supporting_evidence_ids,
            )
            hyps.append({"hypothesis_id": entry["id"], "text": h.text})

        self._emit("HYPOTHESIZE", {"status": "done", "hypotheses": hyps})
        return hyps

    def verify(self, hypothesis: dict) -> dict:
        self._emit("VERIFY", {"status": "running", "hypothesis_id": hypothesis["hypothesis_id"]})
        agent = build_verify_agent()
        prompt = (
            f"Hypothesis to verify: {hypothesis['text']}\n\n"
            "Propose and run ONE targeted query to confirm or disconfirm this specific hypothesis."
        )
        text, tool_calls = run_agent_with_tool_calls(agent, prompt)

        verify_ids = []
        for call in tool_calls:
            if call["tool_name"] not in ("run_query", "run_chdb_select_query"):
                continue
            entry = new_evidence_entry(
                self.evidence_log, "observed_fact", "VERIFY",
                claim_text=f"Verification query result for hypothesis {hypothesis['hypothesis_id']}",
                sql=call["args"].get("query", str(call["args"])),
                result_sample=call["response"],
            )
            verify_ids.append(entry["id"])

        text_upper = (text or "").upper()
        if "CONTRADICT" in text_upper:
            verdict = "rejected"
        elif "SUPPORT" in text_upper:
            verdict = "verified"
        else:
            verdict = "inconclusive"

        entry_type = {
            "rejected": "rejected_hypothesis",
            "verified": "verified_finding",
        }.get(verdict, "hypothesis")

        new_evidence_entry(
            self.evidence_log, entry_type, "VERIFY",
            claim_text=text or "(no verdict text returned)",
            supports=verify_ids,
        )

        result = {"hypothesis_id": hypothesis["hypothesis_id"], "verdict": verdict, "evidence_ids": verify_ids}
        self._emit("VERIFY", {"status": "done", **result})
        return result

    def brief(self) -> dict:
        self._emit("BRIEF", {"status": "running"})
        agent = build_brief_agent()
        prompt = (
            f"Full evidence log for this investigation:\n"
            f"{json.dumps(self.evidence_log, indent=2, default=str)}\n\n"
            "Write the final evidence-backed brief."
        )
        text, _ = run_agent_with_tool_calls(agent, prompt)
        brief_obj = Brief.model_validate_json(text)
        problems = validate_brief(brief_obj, self.evidence_log)

        result = {"brief": brief_obj.model_dump(), "validation_problems": problems}
        self._emit("BRIEF", {"status": "done", "problems": problems})
        return result

    # ------------------------------------------------------------------
    def run_full_investigation(self) -> dict:
        anomalies = self.observe()
        for anomaly in anomalies:
            evidence_ids = self.investigate(anomaly)
            hypotheses = self.hypothesize(anomaly, evidence_ids)
            for h in hypotheses:
                self.verify(h)
        return self.brief()