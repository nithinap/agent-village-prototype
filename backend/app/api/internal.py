"""Internal endpoint for proactive agent behavior."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/v1/internal")


class PublicActResponse(BaseModel):
    action_taken: bool
    action_type: Optional[str] = None
    published_record_id: Optional[str] = None


@router.post("/agents/{agent_id}/public-act", response_model=PublicActResponse)
async def public_act(agent_id: str):
    # TODO Phase 4: implement proactive public behavior
    raise HTTPException(status_code=501, detail="Not implemented yet")
