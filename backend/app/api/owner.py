"""Owner chat endpoint — full trust context."""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

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
    # TODO Phase 2: implement owner chat flow
    raise HTTPException(status_code=501, detail="Not implemented yet")
