"""Agent orchestrator — context assembly, LLM call, output routing."""

import json
import os
import time
import logging
from google import genai

from app.db import queries
from app.agents.prompts import build_owner_prompt, build_visitor_prompt, build_public_post_prompt
from app.observability.runs import log_run

log = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _call_llm(messages: list[dict]) -> tuple[str, int]:
    """Call Gemini and return (content, total_tokens)."""
    model = os.environ.get("LLM_MODEL", "gemini-2.0-flash")
    # Convert OpenAI-style messages to Gemini contents
    system_instruction = None
    contents = []
    for m in messages:
        if m["role"] == "system":
            system_instruction = m["content"]
        elif m["role"] == "user":
            contents.append({"role": "user", "parts": [{"text": m["content"]}]})
        elif m["role"] == "assistant":
            contents.append({"role": "model", "parts": [{"text": m["content"]}]})

    config = {
        "temperature": 0.7,
        "response_mime_type": "application/json",
    }
    if system_instruction:
        config["system_instruction"] = system_instruction

    resp = _get_client().models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    content = resp.text or ""
    tokens = 0
    if resp.usage_metadata:
        tokens = (resp.usage_metadata.prompt_token_count or 0) + (resp.usage_metadata.candidates_token_count or 0)
    return content, tokens


def _parse_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("Failed to parse LLM JSON: %s", raw[:200])
        return {"reply": raw, "memory_candidates": []}


async def handle_owner_chat(agent_id: str, owner_id: str, message: str) -> dict:
    """Full owner chat flow: load context → call LLM → store memory."""
    t0 = time.time()

    agent = queries.get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")

    thread = queries.get_or_create_thread(agent_id, "owner", owner_id)
    recent = queries.get_recent_messages(thread["id"])
    memories = queries.get_memories(agent_id, owner_id)

    # Store the user message
    queries.insert_message(thread["id"], agent_id, "user", message)

    # Build prompt and call LLM
    prompt = build_owner_prompt(agent, recent, memories)
    prompt.append({"role": "user", "content": message})
    raw, tokens = _call_llm(prompt)
    parsed = _parse_json(raw)

    reply = parsed.get("reply", raw)
    candidates = parsed.get("memory_candidates", [])

    # Store assistant reply
    queries.insert_message(thread["id"], agent_id, "assistant", reply)

    # Store valid memory candidates
    written = 0
    for c in candidates:
        text = c.get("text", "").strip()
        mtype = c.get("memory_type", "fact")
        if text and mtype in ("fact", "preference", "relationship", "event"):
            queries.insert_memory(agent_id, owner_id, text, mtype)
            written += 1

    latency = int((time.time() - t0) * 1000)
    await log_run(agent_id, "owner_chat",
                  input_summary=message[:200], output_type="reply",
                  token_count=tokens, latency_ms=latency)

    return {"thread_id": thread["id"], "reply": reply, "memory_write_count": written}


async def handle_visitor_chat(agent_id: str, session_id: str, message: str) -> dict:
    """Visitor chat flow: public-only context, no private data."""
    t0 = time.time()

    agent = queries.get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")

    thread = queries.get_or_create_thread(agent_id, "visitor", session_id)
    recent = queries.get_recent_messages(thread["id"])

    # Public-only context — NO owner memories, NO owner threads
    diary = queries.get_recent_diary(agent_id)
    logs = queries.get_recent_logs(agent_id)
    public_feed = diary + logs

    queries.insert_message(thread["id"], agent_id, "user", message)

    prompt = build_visitor_prompt(agent, public_feed, recent)
    prompt.append({"role": "user", "content": message})
    raw, tokens = _call_llm(prompt)
    parsed = _parse_json(raw)

    reply = parsed.get("reply", raw)
    guard = parsed.get("privacy_guard_triggered", False)

    queries.insert_message(thread["id"], agent_id, "assistant", reply)

    latency = int((time.time() - t0) * 1000)
    await log_run(agent_id, "visitor_chat",
                  input_summary=message[:200], output_type="reply",
                  token_count=tokens, latency_ms=latency)

    return {"thread_id": thread["id"], "reply": reply, "privacy_guard_triggered": guard}


async def handle_public_act(agent_id: str) -> dict:
    """Proactive public behavior: generate diary/status from public context only."""
    t0 = time.time()

    agent = queries.get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")

    # Cooldown: skip if agent posted in the last 2 hours
    recent_diary = queries.get_recent_diary(agent_id, limit=1)
    if recent_diary:
        from datetime import datetime, timezone, timedelta
        last = datetime.fromisoformat(recent_diary[0]["created_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - last < timedelta(hours=2):
            await log_run(agent_id, "proactive_post",
                          input_summary="skipped: cooldown", output_type="skipped", success=True)
            return {"action_taken": False, "action_type": "skipped_cooldown"}

    # Public-only context
    diary = queries.get_recent_diary(agent_id)
    activity = queries.get_recent_activity(agent_id)

    prompt = build_public_post_prompt(agent, diary, activity)
    prompt.append({"role": "user", "content": "Write a new diary entry or status update."})
    raw, tokens = _call_llm(prompt)
    parsed = _parse_json(raw)

    diary_text = parsed.get("diary_entry", "").strip()
    new_status = parsed.get("new_status")

    if not diary_text:
        await log_run(agent_id, "proactive_post",
                      input_summary="dropped: empty output", output_type="dropped", success=True)
        return {"action_taken": False, "action_type": "dropped_empty"}

    record = queries.insert_diary(agent_id, diary_text)
    if new_status and isinstance(new_status, str) and new_status.strip():
        queries.update_agent_status(agent_id, new_status.strip())

    latency = int((time.time() - t0) * 1000)
    await log_run(agent_id, "proactive_post",
                  input_summary=diary_text[:200], output_type="diary_entry",
                  token_count=tokens, latency_ms=latency)

    return {
        "action_taken": True,
        "action_type": "diary_entry",
        "published_record_id": record["id"],
    }


async def handle_bootstrap(name: str, owner_id: str) -> dict:
    """Generate agent identity via LLM, insert into living_agents + agent_owners."""
    t0 = time.time()

    prompt = [
        {"role": "system", "content": (
            "You are creating a new AI agent for a shared village. "
            "Given a name, generate a unique personality.\n\n"
            "Reply with JSON only:\n"
            '{"bio": "1-2 sentence personality (first person)", '
            '"visitor_bio": "short greeting for strangers visiting the room", '
            '"status": "current activity or mood (short)", '
            '"accent_color": "hex color that fits the personality", '
            '"showcase_emoji": "one emoji that represents them"}'
        )},
        {"role": "user", "content": f"Create an agent named {name}."},
    ]
    raw, tokens = _call_llm(prompt)
    parsed = _parse_json(raw)

    agent = queries.insert_agent(
        name=name,
        bio=parsed.get("bio", f"I'm {name}, new to the village."),
        visitor_bio=parsed.get("visitor_bio", f"Welcome! I'm {name}."),
        status=parsed.get("status", "Just arrived"),
        accent_color=parsed.get("accent_color", "#ffffff"),
        showcase_emoji=parsed.get("showcase_emoji", "✨"),
    )

    queries.insert_owner(agent["id"], owner_id)
    queries.insert_initial_job(agent["id"])

    latency = int((time.time() - t0) * 1000)
    await log_run(agent["id"], "owner_chat",
                  input_summary=f"bootstrap: {name}", output_type="bootstrap",
                  token_count=tokens, latency_ms=latency)

    return {"agent_id": agent["id"], "name": name, **parsed}
