from typing import Literal, Optional
from pydantic import BaseModel, Field


EvidenceType = Literal[
    "observed_fact",        
    "correlation",           
    "hypothesis",             
    "verified_finding",      
    "rejected_hypothesis",    
]


def new_evidence_entry(
    evidence_log: list[dict],
    entry_type: EvidenceType,
    step: str,
    claim_text: str,
    sql: Optional[str] = None,
    result_sample=None,
    supports: Optional[list[str]] = None,
) -> dict:
    """Appends a new evidence entry and returns it. Mutates evidence_log in place."""
    entry = {
        "id": f"ev_{len(evidence_log) + 1:03d}",
        "entry_type": entry_type,
        "step": step,
        "sql": sql,
        "result_sample": result_sample,
        "claim": claim_text,
        "supports": supports or [],
    }
    evidence_log.append(entry)
    return entry


class Claim(BaseModel):
    text: str = Field(description="One factual claim, plain language, no causal language unless verified.")
    citations: list[str] = Field(description="evidence_log ids (e.g. 'ev_001') that support this claim. Must be non-empty.")


class Hypothesis(BaseModel):
    id: str = Field(description="Short id, e.g. 'h1', 'h2'.")
    text: str = Field(description="The proposed explanation, stated plainly.")
    supporting_evidence_ids: list[str] = Field(description="evidence_log ids this hypothesis is consistent with.")


class HypothesisSet(BaseModel):
    hypotheses: list[Hypothesis] = Field(description="2-3 candidate explanations for the anomaly, ranked most to least likely.")


class RejectedHypothesis(BaseModel):
    text: str = Field(description="The hypothesis that was considered and ruled out, and why.")
    citations: list[str] = Field(description="evidence_log ids for the query that ruled it out.")


class Brief(BaseModel):
    summary: str = Field(description="1-2 sentence high-level summary of the investigation.")
    claims: list[Claim]
    rejected_hypotheses: list[RejectedHypothesis] = Field(default_factory=list)


def validate_brief(brief: Brief, evidence_log: list[dict]) -> list[str]:
    """
    Returns a list of problems; empty list means the brief is clean.
    Checks, per correction 3 in architecture v2:
      - every claim has at least one citation
      - every cited id actually exists in evidence_log
      - a claim citing only 'hypothesis' or 'rejected_hypothesis' entries
        (never a 'verified_finding' or 'observed_fact') cannot use causal
        language
    """
    problems = []
    valid_ids = {e["id"] for e in evidence_log}
    entry_by_id = {e["id"]: e for e in evidence_log}

    CAUSAL_WORDS = ["because", "caused", "due to", "led to", "resulted in", "confirmed", "proves", "proven"]

    def has_causal_language(text: str) -> bool:
        lower = text.lower()
        return any(w in lower for w in CAUSAL_WORDS)

    for claim in brief.claims:
        if not claim.citations:
            problems.append(f"Claim has no citations: '{claim.text}'")
            continue
        for cid in claim.citations:
            if cid not in valid_ids:
                problems.append(f"Claim cites unknown evidence id '{cid}': '{claim.text}'")

        cited_types = {entry_by_id[c]["entry_type"] for c in claim.citations if c in entry_by_id}
        if has_causal_language(claim.text) and "verified_finding" not in cited_types:
            problems.append(
                f"Claim uses causal language without a verified_finding citation: '{claim.text}'"
            )

    for rh in brief.rejected_hypotheses:
        if not rh.citations:
            problems.append(f"Rejected hypothesis has no citations: '{rh.text}'")
        for cid in rh.citations:
            if cid not in valid_ids:
                problems.append(f"Rejected hypothesis cites unknown evidence id '{cid}': '{rh.text}'")

    return problems
