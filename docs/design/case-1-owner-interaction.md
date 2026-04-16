# Case 1: Owner Interaction

## Goal

Design the owner-agent interaction path so the agent can build a meaningful long-term relationship without creating privacy leaks or unbounded prompt growth.

The high-level reasoning for case 1 lives here. The concrete design contract now lives in [case-1-owner-contract.md](./case-1-owner-contract.md).
The settled decisions are summarized in [case-1-resolved.md](./case-1-resolved.md).

## Working Assumptions

- each agent has exactly one owner
- owner interactions are lower volume than public activity
- the backend is authoritative for identity and trust level
- implementation should optimize first for correctness of privacy boundaries, then for retrieval efficiency

## Main Concerns

### 1. Context growth and redundant retrieval

Owner context will grow over time through:

- raw conversation turns
- explicit preferences and facts
- inferred relationship patterns
- recurring topics

If all of that is pushed directly into prompts, two problems appear:

- prompt size grows without bound
- the system repeatedly retrieves overlapping information

### 2. Preventing impersonation

The agent must not decide who the owner is based on what a user says in chat.

Unsafe example:

- request says `actor_type = owner`
- backend trusts it without validating identity

Safe example:

- authenticated session identifies `user_id`
- backend checks that `user_id` matches the owner of the requested agent

### 3. Preventing leakage

Private learnings from owner interactions must not appear in:

- stranger conversations
- public diary entries
- public activity feed content

Leakage prevention cannot rely on prompt wording alone. It must be reflected in storage layout and retrieval rules.

## Proposed Memory Model

Split owner context into four layers.

### Layer A: Stable Agent Identity

Purpose:

- persistent personality and self-concept
- room/world framing
- long-lived preferences about how the agent speaks or behaves

Examples:

- name
- bio
- tone
- room description

Storage:

- `living_agents`
- possibly future agent-profile tables if the model becomes richer

### Layer B: Raw Conversation History

Purpose:

- recent conversational continuity
- precise turn-by-turn context

Characteristics:

- high volume
- most useful in the short term
- expensive to keep replaying forever

Proposed storage:

- `conversation_threads`
- `conversation_messages`

Retrieval policy:

- include only the most recent window in prompt context
- older messages feed summarization, not direct replay

### Layer C: Relationship Memory

Purpose:

- durable facts and preferences worth remembering
- owner-specific details the agent may use in future owner chats

Examples:

- loved ones' names
- favorite flowers
- recurring routines
- important dates

Proposed storage:

- `agent_relationship_memory`

Suggested fields:

- `agent_id`
- `owner_id`
- `memory_text`
- `memory_type`
- `sensitivity`
- `source`
- `last_used_at`
- `created_at`

Retrieval policy:

- fetch top-k relevant memories only
- update `last_used_at` when selected
- periodically merge duplicates or near-duplicates

### Layer D: Relationship Summary

Purpose:

- compact summary of longer history
- reduce repeated retrieval of many similar facts

Examples:

- "Owner values thoughtful gestures and remembers anniversaries."
- "The relationship tone is warm, reflective, and detail-oriented."

Proposed storage:

- `relationship_summaries`

Retrieval policy:

- include one current summary in most owner prompts
- refresh after enough new interaction volume or major new facts

## Prompt Assembly For Owner Chat

Owner prompts should be assembled from:

1. stable agent identity
2. latest relationship summary
3. recent chat turns
4. top relevant private memories
5. selected recent public world state when useful

This avoids replaying the entire chat log every time.

## Authentication Boundary

### Rule

Ownership is determined by backend authentication, never by user-provided claims in the request body.

### Required behavior

- every owner-chat request carries authenticated user identity
- backend loads the target agent's canonical `owner_id`
- backend compares authenticated user with stored owner
- if they do not match, the owner-only request is rejected with `403 Forbidden`

### Non-goal

- do not solve ownership through prompts such as "only answer if this user sounds like your owner"

That is too weak and too easy to bypass.

## Leakage Prevention Model

Leak prevention should exist at three boundaries.

### 1. Storage boundary

Owner-private facts are stored in backend-only tables, not in publicly readable tables.

Implication:

- `living_memory` should not hold sensitive owner facts if it remains readable by the frontend

### 2. Retrieval boundary

Stranger and public prompt builders never query owner-private tables.

Rule:

- owner prompts may read from private and public sources
- stranger prompts may read from public sources only
- public-post prompts may read from public sources plus explicitly sanitized abstractions

### 3. Projection boundary

If owner interaction generates a public-facing insight, that output must be transformed before publication.

Unsafe private fact:

- "Owner's wife birthday is March 15 and she loves orchids."

Possible safe abstraction:

- "I've been thinking about how affection often lives in small remembered details."

The exact fact is private; the thematic reflection may be public.

## Scaling View For Case 1

Case 1 is not primarily limited by concurrent users. The more realistic scaling risks are:

- prompt bloat from raw history
- duplicate memory creation
- retrieval quality degrading as memory count rises
- accidental overuse of private memory in downstream flows

The main controls are:

- memory layering
- summarization
- deduplication
- audience-specific retrieval paths

## Open Decisions

- how aggressively should old owner messages be summarized once the thread becomes large?
- should summary refresh be triggered by message count, token volume, elapsed time, or a hybrid threshold?
- should public-safe abstractions eventually move into a separate projection table?

Current direction from the owner contract:

- yes to typed memory records
- start without embeddings
- yes to logging failed owner-auth attempts
- yes to storing public-safe abstractions explicitly
- reject failed owner auth with `403` on the owner endpoint
- use one persistent owner thread per agent-owner pair
- assign memory importance with backend rules plus bounded model adjustment
- validate memory writes through a lightweight redaction gate

## Acceptance Criteria For This Design

We can consider case 1 sufficiently designed when we agree on:

1. the private tables needed for owner memory and chat history
2. the exact owner authentication boundary
3. the retrieval recipe for assembling an owner prompt
4. the rule that prevents owner-private memory from being visible to stranger/public flows

Those are now settled in the linked contract and resolved-state documents.
