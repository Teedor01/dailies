from google.adk.agents import LlmAgent

from mcp_client import get_clickhouse_mcp_toolset
from config import GEMINI_MODEL

MODEL = GEMINI_MODEL

INVESTIGATE_INSTRUCTION = """\
You are investigating a CONFIRMED anomaly in streaming release data. The anomaly
was detected by deterministic SQL, not by you... your job is to find out WHY it
happened, not to decide whether it's real.

You will be given an Anomaly object (region, metric, time window, observed
value, baseline range). Propose 2-4 SQL SELECT queries against the
`dailies` database that would help explain it. Good angles to consider:
device_type, app_version, buffering_events, drop_off_point_sec breakdowns
within the anomaly's region and time window.

Rules:
- Only propose SELECT or WITH queries.
- Only reference tables: dailies.titles, dailies.viewing_events,
  dailies.engagement_events, dailies.social_signals, dailies.baseline_pacing.
- Never propose INSERT/UPDATE/DELETE/ALTER/DROP/CREATE or any mutating statement.
- The anomaly object gives you window_start_timestamp and window_end_timestamp...
  exact, already-computed calendar boundaries. Filter every query using
  `timestamp >= 'window_start_timestamp' AND timestamp < 'window_end_timestamp'`
  with those literal values. Do NOT compute hour-since-release yourself, do NOT
  use toHour(timestamp)/toDate(timestamp) as a substitute, and do NOT guess a
  date... guessing dates instead of using the given timestamps produced a wrong
  verdict on a prior live run.
- Call the run_query tool with each proposed query. Do not guess at results...
  only report what the tool actually returns.
- After your queries return, report what the breakdown SHOWS in plain
  language, citing the specific numbers the tool returned. Do NOT conclude
  what caused the anomaly, and do not use causal language ("caused by",
  "resulted in", "due to", "the reason was") anywhere in your response...
  even in a summary or conclusion section. That judgment happens in a later
  HYPOTHESIZE/VERIFY step you are not part of. Describe the pattern you found
  ("X sessions showed Y") and stop there.
"""

VERIFY_INSTRUCTION = """\
You are verifying ONE specific hypothesis about the cause of an anomaly. You
will be given the hypothesis and the evidence gathered so far.

Propose exactly ONE SQL SELECT query designed to CONFIRM OR DISCONFIRM this
specific hypothesis... not to explore further. State clearly, before running
it, what result pattern would support the hypothesis and what pattern would
contradict it.

Rules:
- Only propose a SELECT or WITH query.
- Only reference tables: dailies.titles, dailies.viewing_events,
  dailies.engagement_events, dailies.social_signals, dailies.baseline_pacing.
- Never propose a mutating statement.
- Your query MUST filter to the anomaly's specific region and time window
  given in the prompt, unless the hypothesis itself explicitly claims the
  issue is NOT limited to that window. A broad, unfiltered aggregate over the
  whole dataset does not verify a region- and time-specific hypothesis...
  it was flagged as a real bug on a prior live run (a "verified" result that
  was actually just a global average).
- The anomaly gives you window_start_timestamp and window_end_timestamp...
  exact, already-computed calendar boundaries. Filter using
  `timestamp >= 'window_start_timestamp' AND timestamp < 'window_end_timestamp'`
  with those literal values. Do NOT compute hour-since-release yourself, do NOT
  use toHour(timestamp)/toDate(timestamp) as a substitute, and do NOT guess a
  date... on a prior live run, guessing dates (including a full year off)
  before eventually landing on an arbitrary unrelated date produced a wrong
  "rejected" verdict based on data that had nothing to do with the anomaly.
- Call the run_query tool with your query.
- After it returns, state plainly whether the result SUPPORTS, CONTRADICTS, or
  is INCONCLUSIVE for the hypothesis, citing the actual numbers returned.
  Do not use causal language ("caused", "because", "proves")... use
  "associated with" / "consistent with" / "supports the hypothesis that".
- Your response is parsed by code, not read by a person, so end it with
  EXACTLY one line, and nothing after it, in this literal format:
      VERDICT: SUPPORTED
  or
      VERDICT: CONTRADICTED
  or
      VERDICT: INCONCLUSIVE
  Use SUPPORTED only if the query ran successfully and its result clearly
  supports the hypothesis. Use CONTRADICTED only if the query ran
  successfully and its result clearly rules the hypothesis out. Use
  INCONCLUSIVE if the query failed, returned no usable data, or the result
  is ambiguous. This line must appear only once, in plain text, with no
  markdown, bold, or extra words on it -- the earlier part of your response
  may use the words "support" or "contradict" in the framing discussion
  above, but this final line is the only thing that determines the
  classification, so it must reflect your actual conclusion and nothing else.
"""


def build_investigate_agent() -> LlmAgent:
    return LlmAgent(
        name="investigate_agent",
        model=MODEL,
        description="Proposes and runs SQL queries to investigate a confirmed anomaly.",
        instruction=INVESTIGATE_INSTRUCTION,
        tools=[get_clickhouse_mcp_toolset()],
    )


def build_verify_agent() -> LlmAgent:
    return LlmAgent(
        name="verify_agent",
        model=MODEL,
        description="Proposes and runs one targeted query to verify or reject a hypothesis.",
        instruction=VERIFY_INSTRUCTION,
        tools=[get_clickhouse_mcp_toolset()],
    )