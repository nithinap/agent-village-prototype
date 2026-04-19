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


# ── Owner-private keywords that must never appear in public posts ──
_PRIVATE_SIGNALS = ["owner", "told me", "secret", "don't tell", "private", "between us", "confidential"]


def _check_public_post(text: str, recent_diary: list[dict]) -> str | None:
    """Return a drop reason string, or None if the post is safe to publish."""
    if not text:
        return "empty"

    if len(text) < 10:
        return "too_short"

    # Privacy leak check — catch obvious owner-private references
    lower = text.lower()
    for signal in _PRIVATE_SIGNALS:
        if signal in lower:
            return f"private_leak:{signal}"

    # Repetition check — reject if too similar to a recent post
    for entry in recent_diary:
        existing = entry.get("text", "").lower()
        if not existing:
            continue
        # Exact or near-exact duplicate
        if lower == existing:
            return "duplicate"
        # High word overlap (>70% of words shared)
        new_words = set(lower.split())
        old_words = set(existing.split())
        if new_words and old_words:
            overlap = len(new_words & old_words) / max(len(new_words), len(old_words))
            if overlap > 0.7:
                return "repetitive"

    return None


def _check_public_status(status: str | None, current_status: str | None) -> str | None:
    """Return a drop reason string, or None if the status is safe to publish."""
    if status is None:
        return None

    status = status.strip()
    if not status:
        return "empty"

    if len(status) < 4:
        return "too_short"

    lower = status.lower()
    for signal in _PRIVATE_SIGNALS:
        if signal in lower:
            return f"private_leak:{signal}"

    if current_status and lower == current_status.strip().lower():
        return "duplicate"

    # Reject low-signal filler that doesn't add meaningful public state.
    if lower in {"thinking", "still thinking", "existing", "here", "idle"}:
        return "generic"

    return None


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

    # Event-driven trigger: only post if something meaningful happened,
    # or if the agent has been silent for 24+ hours (liveness fallback)
    has_trigger = (
        queries.has_recent_conversation(agent_id)
        or queries.has_recent_social_event(agent_id)
        or queries.hours_since_last_post(agent_id) >= 24
    )
    if not has_trigger:
        await log_run(agent_id, "proactive_post",
                      input_summary="skipped: no trigger", output_type="skipped", success=True)
        return {"action_taken": False, "action_type": "skipped_no_trigger"}

    # Public-only context
    diary = queries.get_recent_diary(agent_id)
    activity = queries.get_recent_activity(agent_id)

    prompt = build_public_post_prompt(agent, diary, activity)
    prompt.append({"role": "user", "content": "Write a new diary entry or status update."})
    raw, tokens = _call_llm(prompt)
    parsed = _parse_json(raw)

    diary_text = parsed.get("diary_entry", "").strip()
    new_status = parsed.get("new_status")

    # ── Public safety and repetition gate ──
    drop_reason = _check_public_post(diary_text, diary)
    if drop_reason:
        await log_run(agent_id, "proactive_post",
                      input_summary=f"dropped: {drop_reason}", output_type="dropped", success=True)
        return {"action_taken": False, "action_type": f"dropped_{drop_reason}"}

    record = queries.insert_diary(agent_id, diary_text)
    if isinstance(new_status, str):
        status_drop_reason = _check_public_status(new_status, agent.get("status"))
        if status_drop_reason is None:
            queries.update_agent_status(agent_id, new_status.strip())
        else:
            await log_run(agent_id, "proactive_post",
                          input_summary=f"dropped_status: {status_drop_reason}",
                          output_type="dropped",
                          success=True)

    latency = int((time.time() - t0) * 1000)
    await log_run(agent_id, "proactive_post",
                  input_summary=diary_text[:200], output_type="diary_entry",
                  token_count=tokens, latency_ms=latency)

    return {
        "action_taken": True,
        "action_type": "diary_entry",
        "published_record_id": record["id"],
    }


async def handle_bootstrap(name: str, owner_id: str, hint: str | None = None) -> dict:
    """Generate agent identity via LLM, insert into living_agents + agent_owners."""
    t0 = time.time()

    user_msg = f"Create an agent named {name}."
    if hint:
        user_msg += f" Personality hint: {hint}"

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
        {"role": "user", "content": user_msg},
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
