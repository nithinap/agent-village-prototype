"""Owner chat endpoint — full trust context."""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.db.queries import get_owner_id
from app.agents.orchestrator import handle_owner_chat

router = APIRouter(prefix="/v1/owner")


class OwnerChatRequest(BaseModel):
    message: str
    client_context: Optional[dict] = None


class OwnerChatResponse(BaseModel):
    thread_id: str
    reply: str
    memory_write_count: int = 0


@router.post("/agents/{agent_id}/chat", response_model=OwnerChatResponse)
async def owner_chat(
    agent_id: str,
    body: OwnerChatRequest,
    x_owner_id: str = Header(...),
):
    # Auth: check X-Owner-Id against agent_owners
    canonical_owner = get_owner_id(agent_id)
    if not canonical_owner or canonical_owner != x_owner_id:
        raise HTTPException(status_code=403, detail="You are not the owner of this agent.")

    result = await handle_owner_chat(agent_id, x_owner_id, body.message)
    return OwnerChatResponse(**result)
