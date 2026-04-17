"""Background worker that polls agent_jobs and triggers proactive behavior."""

import asyncio
import logging

log = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 15


async def run_worker():
    """Main worker loop — polls agent_jobs for due public_act jobs."""
    log.info("Worker started, polling every %ds", POLL_INTERVAL_SECONDS)
    while True:
        try:
            # TODO Phase 4: poll agent_jobs, call handle_public_act per agent
            pass
        except Exception:
            log.exception("Worker tick failed")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
