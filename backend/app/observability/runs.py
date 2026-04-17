"""Lightweight logger for agent_runs observability table."""

import uuid
import time
from typing import Optional
from app.db.client import get_supabase


async def log_run(
    agent_id: str,
    run_type: str,
    *,
    input_summary: Optional[str] = None,
    output_type: Optional[str] = None,
    token_count: Optional[int] = None,
    latency_ms: Optional[int] = None,
    success: bool = True,
    error: Optional[str] = None,
) -> str:
    run_id = str(uuid.uuid4())
    get_supabase().table("agent_runs").insert({
        "id": run_id,
        "agent_id": agent_id,
        "run_type": run_type,
        "input_summary": input_summary,
        "output_type": output_type,
        "token_count": token_count,
        "latency_ms": latency_ms,
        "success": success,
        "error": error,
    }).execute()
    return run_id
