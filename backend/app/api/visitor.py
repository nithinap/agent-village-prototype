"""Visitor chat endpoint — limited trust, no private data."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.agents.orchestrator import handle_visitor_chat

router = APIRouter(prefix="/v1/visitor")


class VisitorChatRequest(BaseModel):
    message: str
    visitor_session_id: str
    client_context: Optional[dict] = None


class VisitorChatResponse(BaseModel):
    thread_id: str
    reply: str
    privacy_guard_triggered: bool = False


@router.post("/agents/{agent_id}/chat", response_model=VisitorChatResponse)
async def visitor_chat(
    agent_id: str,
    body: VisitorChatRequest,
):
    result = await handle_visitor_chat(agent_id, body.visitor_session_id, body.message)
    return VisitorChatResponse(**result)
