"""
pure_reasoner.py

The second (and last) LlmAgent in the pipeline. Deliberately has NO tools --
it can only reason over the evidence_log text it's given in the prompt. Used
twice by controller.py:
  - HYPOTHESIZE: propose 2-3 candidate explanations for an anomaly
  - BRIEF: write the final evidence-backed report

Both steps use output_schema (structured output) so Gemini's response is
forced into a checkable shape rather than free text -- see evidence.py for
the HypothesisSet and Brief schemas, and validate_brief() for the citation
check that runs on the BRIEF output before it reaches the UI.
"""

from google.adk.agents import LlmAgent

from evidence import HypothesisSet, Brief
from config import GEMINI_MODEL

# See tool_reasoner.py for the model-choice history (gemini-2.5-flash 404'd,
# gemini-3.6-flash's free tier is only 20 requests/day). Set via GEMINI_MODEL
# in .env -- default gemini-2.5-flash-lite.
MODEL = GEMINI_MODEL

HYPOTHESIZE_INSTRUCTION = """\
You are proposing candidate explanations for a confirmed, investigated anomaly.
You will be given the anomaly and the evidence gathered during investigation
(as a list of evidence_log entries, each with an id, a SQL query, and a result).

Propose 2-3 hypotheses that would explain the anomaly, ranked most to least
likely given the evidence. Each hypothesis must cite the evidence_log ids it is
consistent with -- use ONLY the ids given to you, do not invent ids or refer to
data you were not given.

Some evidence_log entries have entry_type "query_error" -- these are queries
that FAILED to execute. They are not data and contain no findings. Never cite
a query_error entry as support for a hypothesis; ignore them when reasoning.

Do not claim any hypothesis is confirmed -- that determination happens in a
later verification step you are not part of. State them as open possibilities.
"""

BRIEF_INSTRUCTION = """\
You are writing the final evidence-backed briefing for a release-monitoring
team. You will be given: the anomaly, the full evidence_log (observed facts,
correlations, verified findings, and rejected hypotheses), all with ids.

Some evidence_log entries have entry_type "query_error" -- these are queries
that FAILED to execute. They are not data and contain no findings. Never cite
a query_error entry in a claim or rejected_hypothesis; ignore them entirely.

Write:
  - summary: 1-2 sentences, plain language, no jargon.
  - claims: each individual factual statement, with citations to the
    evidence_log ids that support it. EVERY claim must have at least one
    citation -- if you cannot cite it, do not state it.
  - rejected_hypotheses: any hypothesis that was investigated and ruled out,
    stated explicitly as rejected, with the citation for why.

Language rules (these will be checked mechanically -- follow them exactly,
INCLUDING in the summary field, not just in claims):
  - Only use causal language ("because", "caused", "led to", "due to") for a
    claim that cites a 'verified_finding' entry. Never for a hypothesis or
    correlation, and never in the top-level summary even if it's restating a
    verified finding -- keep the summary to "evidence points to X" / "X was
    associated with Y", save causal framing for the specific cited claim.
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