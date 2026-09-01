from google.adk.agents import LlmAgent

from evidence import HypothesisSet, Brief


MODEL = "gemini-3.6-flash"

HYPOTHESIZE_INSTRUCTION = """\
You are proposing candidate explanations for a confirmed, investigated anomaly.
You will be given the anomaly and the evidence gathered during investigation
(as a list of evidence_log entries, each with an id, a SQL query, and a result).

Propose 2-3 hypotheses that would explain the anomaly, ranked most to least
likely given the evidence. Each hypothesis must cite the evidence_log ids it is
consistent with -- use ONLY the ids given to you, do not invent ids or refer to
data you were not given.

Do not claim any hypothesis is confirmed -- that determination happens in a
later verification step you are not part of. State them as open possibilities.
"""

BRIEF_INSTRUCTION = """\
You are writing the final evidence-backed briefing for a release-monitoring
team. You will be given: the anomaly, the full evidence_log (observed facts,
correlations, verified findings, and rejected hypotheses), all with ids.

Write:
  - summary: 1-2 sentences, plain language, no jargon.
  - claims: each individual factual statement, with citations to the
    evidence_log ids that support it. EVERY claim must have at least one
    citation -- if you cannot cite it, do not state it.
  - rejected_hypotheses: any hypothesis that was investigated and ruled out,
    stated explicitly as rejected, with the citation for why.

Language rules (these will be checked mechanically -- follow them exactly):
  - Only use causal language ("because", "caused", "led to") for a claim that
    cites a 'verified_finding' entry. Never for a hypothesis or correlation.
  - For correlations, say "co-occurred with" / "was associated with" /
    "coincided with" -- never "caused".
  - For verified findings, say "evidence supports the hypothesis that..." --
    never "confirmed" or "proven".
  - Do not state any number that does not appear in a cited evidence_log
    entry's result.
"""


def build_hypothesize_agent() -> LlmAgent:
    return LlmAgent(
        name="hypothesize_agent",
        model=MODEL,
        description="Proposes candidate explanations for an anomaly from existing evidence only.",
        instruction=HYPOTHESIZE_INSTRUCTION,
        output_schema=HypothesisSet,
    )


def build_brief_agent() -> LlmAgent:
    return LlmAgent(
        name="brief_agent",
        model=MODEL,
        description="Writes the final evidence-backed brief with per-claim citations.",
        instruction=BRIEF_INSTRUCTION,
        output_schema=Brief,
    )