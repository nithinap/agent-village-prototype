"""Agent orchestrator — context assembly, LLM call, output routing."""

import json
import os
import time
import logging
from openai import OpenAI

from app.db import queries
from app.agents.prompts import build_owner_prompt, build_visitor_prompt, build_public_post_prompt
from app.observability.runs import log_run

log = logging.getLogger(__name__)

_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def _call_llm(messages: list[dict]) -> tuple[str, int]:
    """Call OpenAI and return (content, total_tokens)."""
    resp = _client.chat.completions.create(
        model=_model,
        messages=messages,
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    tokens = resp.usage.total_tokens if resp.usage else 0
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
    # TODO Phase 3
    raise NotImplementedError


async def handle_public_act(agent_id: str) -> dict:
    """Proactive public behavior: generate diary/status from public context."""
    # TODO Phase 4
    raise NotImplementedError
