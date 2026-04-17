"""Agent orchestrator — context assembly, LLM call, output routing."""


async def handle_owner_chat(agent_id: str, owner_id: str, message: str) -> dict:
    """Full owner chat flow: load context, call LLM, store memory."""
    # TODO Phase 2
    raise NotImplementedError


async def handle_visitor_chat(agent_id: str, session_id: str, message: str) -> dict:
    """Visitor chat flow: public-only context, no private data."""
    # TODO Phase 3
    raise NotImplementedError


async def handle_public_act(agent_id: str) -> dict:
    """Proactive public behavior: generate diary/status from public context."""
    # TODO Phase 4
    raise NotImplementedError
