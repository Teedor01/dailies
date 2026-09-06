"""
runner_helpers.py

Every reasoning step in this project (INVESTIGATE, VERIFY, HYPOTHESIZE, BRIEF)
is a single-turn call to an LlmAgent -- the deterministic controller decides
what happens next, not the agent itself (see architecture v2, Section 3).
This helper wraps the ADK boilerplate (Runner + session + event loop) needed
to make one such call and get back the final text response.

VERIFIED LIVE (Sep 5, full-stack run via api/main.py + web/): a real run made
it through OBSERVE, all of APAC's INVESTIGATE/HYPOTHESIZE/VERIFY (twice), and
into LATAM's INVESTIGATE before hitting a 429 RESOURCE_EXHAUSTED --
GenerateRequestsPerMinutePerProjectPerModel-FreeTier, limit 15/min on
gemini-3.5-flash-lite. This is a PER-MINUTE cap, not the daily cap hit
earlier in the project -- it WILL be hit on every full run regardless of
which free-tier model is used, because this pipeline fires many Gemini calls
back-to-back within seconds. Fixed here with retry-with-backoff that reads
the API's own suggested retry delay out of the error message.
"""

import asyncio
import re
import time
import uuid

from google.adk.runners import InMemoryRunner
from google.genai import types

MAX_RATE_LIMIT_RETRIES = 4
DEFAULT_RETRY_DELAY_SECONDS = 20.0


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc)
    return "RESOURCE_EXHAUSTED" in msg or "429" in msg


def _extract_retry_delay(exc: Exception, default: float = DEFAULT_RETRY_DELAY_SECONDS) -> float:
    """Gemini's 429 body includes e.g. 'retryDelay': '11s' -- use that
    instead of a fixed guess when it's present, plus a small safety margin."""
    match = re.search(r"retryDelay['\"]?:\s*['\"]?(\d+(?:\.\d+)?)s", str(exc))
    if match:
        return float(match.group(1)) + 3.0
    return default


def run_agent_once(agent, user_message: str, app_name: str = "dailies") -> str:
    """
    Runs a single-turn conversation with an ADK agent and returns the final
    text response as a string. Creates a fresh in-memory session per call --
    each reasoning step in this pipeline is stateless by design; the
    deterministic controller (not agent memory) carries context between steps
    via what it puts INTO the prompt each time.
    """
    text, _ = run_agent_with_tool_calls(agent, user_message, app_name)
    return text


def run_agent_with_tool_calls(
    agent, user_message: str, app_name: str = "dailies", max_retries: int = MAX_RATE_LIMIT_RETRIES
):
    """
    Like run_agent_once, but also returns the REAL tool calls made during the
    run -- the actual SQL text sent and the actual result returned. This is
    what evidence_log entries must be built from (see evidence.py) -- Gemini's
    final-text summary is a paraphrase and must never be the source of a
    number in evidence_log; the tool call/response pair is the source of truth.

    Returns (final_text, tool_calls) where tool_calls is a list of dicts:
        {"tool_name": str, "args": dict, "response": Any}

    On a 429 rate-limit error, retries with a FRESH session (not a resumed
    one) up to max_retries times -- resuming the same session after a
    mid-conversation failure risks confusing multi-turn state; a clean retry
    of the same single-turn prompt is simpler and safe here since every call
    in this pipeline is already designed to be a stateless, self-contained
    turn (see controller.py).
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        runner = InMemoryRunner(agent=agent, app_name=app_name)
        user_id = "dailies-controller"
        session_id = str(uuid.uuid4())

        runner.session_service.create_session_sync(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        async def _run():
            content = types.Content(role="user", parts=[types.Part(text=user_message)])
            final_text = None
            tool_calls = []
            pending_calls = {}  # function_call.id -> {"tool_name": ..., "args": ...}

            async for event in runner.run_async(
                user_id=user_id, session_id=session_id, new_message=content
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.function_call:
                            fc = part.function_call
                            pending_calls[fc.id] = {"tool_name": fc.name, "args": dict(fc.args or {})}
                        if part.function_response:
                            fr = part.function_response
                            call_info = pending_calls.get(fr.id, {"tool_name": fr.name, "args": {}})
                            tool_calls.append({
                                "tool_name": call_info["tool_name"],
                                "args": call_info["args"],
                                "response": fr.response,
                            })
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = "".join(p.text for p in event.content.parts if p.text)

            return final_text, tool_calls

        try:
            return asyncio.run(_run())
        except Exception as e:
            if _is_rate_limit_error(e) and attempt < max_retries:
                delay = _extract_retry_delay(e)
                print(
                    f"[runner_helpers] Gemini rate limit hit (attempt {attempt + 1}/{max_retries + 1}) "
                    f"-- retrying in {delay:.0f}s..."
                )
                last_exception = e
                time.sleep(delay)
                continue
            raise

    raise last_exception