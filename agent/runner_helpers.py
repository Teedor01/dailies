import asyncio
import uuid

from google.adk.runners import InMemoryRunner
from google.genai import types


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


def run_agent_with_tool_calls(agent, user_message: str, app_name: str = "dailies"):
    """
    Like run_agent_once, but also returns the REAL tool calls made during the
    run -- the actual SQL text sent and the actual result returned. This is
    what evidence_log entries must be built from (see evidence.py) -- Gemini's
    final-text summary is a paraphrase and must never be the source of a
    number in evidence_log; the tool call/response pair is the source of truth.

    Returns (final_text, tool_calls) where tool_calls is a list of dicts:
        {"tool_name": str, "args": dict, "response": Any}

    UNVERIFIED against a live run as of writing -- function_call/function_response
    field names (fc.id, fc.name, fc.args, fr.response) are confirmed from the
    installed google-genai types, but the exact shape of `response` for an MCP
    tool call specifically (e.g. whether it's a raw string, a dict with a
    'result' key, etc.) has not been observed live. If tool_calls comes back
    with an unexpected response shape, print one raw entry and adjust the
    extraction in controller.py accordingly -- don't guess further from here.
    """
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
        pending_calls = {}  

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

    return asyncio.run(_run())