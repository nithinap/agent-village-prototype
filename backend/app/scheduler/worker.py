"""Background worker that polls agent_jobs and triggers proactive behavior."""

import asyncio
import logging

from app.db import queries
from app.agents.orchestrator import handle_public_act

log = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30


async def run_worker():
    """Main worker loop — polls agent_jobs for due public_act jobs."""
    log.info("Worker started, polling every %ds", POLL_INTERVAL_SECONDS)
    # Small delay to let the app finish starting
    await asyncio.sleep(5)

    while True:
        try:
            jobs = queries.get_due_jobs("public_act")
            if jobs:
                log.info("Found %d due job(s)", len(jobs))

            for job in jobs:
                agent_id = job["agent_id"]
                job_id = job["id"]
                try:
                    queries.lock_job(job_id)
                    result = await handle_public_act(agent_id)
                    queries.complete_job(job_id)
                    queries.reschedule_job(agent_id, "public_act", delay_minutes=120)
                    log.info("Agent %s: %s", agent_id, result.get("action_type", "unknown"))
                except Exception:
                    log.exception("Failed to process job %s for agent %s", job_id, agent_id)

        except Exception:
            log.exception("Worker tick failed")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)
