"""Bootstrap endpoint — create a new agent with LLM-generated identity."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.orchestrator import handle_bootstrap

router = APIRouter(prefix="/v1/agents")


class BootstrapRequest(BaseModel):
    name: str
    owner_id: str


class BootstrapResponse(BaseModel):
    agent_id: str
    name: str
    bio: str
    visitor_bio: str
    status: str
    accent_color: str
    showcase_emoji: str


@router.post("/bootstrap", response_model=BootstrapResponse)
async def bootstrap(body: BootstrapRequest):
    result = await handle_bootstrap(body.name, body.owner_id)
    return BootstrapResponse(**result)
