"""Prompt templates for the three trust contexts."""


def build_owner_prompt(
    agent_profile: dict,
    recent_messages: list[dict],
    memories: list[dict],
) -> list[dict]:
    """Assemble the owner chat prompt with full private context."""
    # TODO Phase 2
    return []


def build_visitor_prompt(
    agent_profile: dict,
    public_feed: list[dict],
    recent_messages: list[dict],
) -> list[dict]:
    """Assemble the visitor chat prompt with public-only context."""
    # TODO Phase 3
    return []


def build_public_post_prompt(
    agent_profile: dict,
    recent_diary: list[dict],
    recent_activity: list[dict],
) -> list[dict]:
    """Assemble the proactive public post prompt."""
    # TODO Phase 4
    return []
