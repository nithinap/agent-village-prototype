"""Internal endpoint for proactive agent behavior."""

import os
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.agents.orchestrator import handle_public_act

router = APIRouter(prefix="/v1/internal")

_INTERNAL_KEY = os.environ.get("INTERNAL_API_KEY")
if not _INTERNAL_KEY:
    raise RuntimeError("INTERNAL_API_KEY environment variable is required")


class PublicActResponse(BaseModel):
    action_taken: bool
    action_type: Optional[str] = None
    published_record_id: Optional[str] = None


@router.post("/agents/{agent_id}/public-act", response_model=PublicActResponse)
async def public_act(agent_id: str, x_internal_key: str = Header()):
    if x_internal_key != _INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Invalid internal key.")
    result = await handle_public_act(agent_id)
    return PublicActResponse(**result)
