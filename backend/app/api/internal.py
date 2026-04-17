"""Internal endpoint for proactive agent behavior."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.agents.orchestrator import handle_public_act

router = APIRouter(prefix="/v1/internal")


class PublicActResponse(BaseModel):
    action_taken: bool
    action_type: Optional[str] = None
    published_record_id: Optional[str] = None


@router.post("/agents/{agent_id}/public-act", response_model=PublicActResponse)
async def public_act(agent_id: str):
    result = await handle_public_act(agent_id)
    return PublicActResponse(**result)
