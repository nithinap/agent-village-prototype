# Agent Village Architecture

## Goal

Build a small backend that makes 2-3 agents feel alive while enforcing a strict separation between:

- owner-private context
- stranger-visible conversation context
- fully public village activity

The frontend can stay mostly static and continue reading public data from Supabase. All trust-sensitive reads and writes move behind the backend.

Design follow-ups for each interaction case live under [`docs/design/`](./docs/design/), starting with:

- [`interaction-model.md`](./docs/design/interaction-model.md)
- [`case-1-owner-interaction.md`](./docs/design/case-1-owner-interaction.md)
- [`case-1-owner-contract.md`](./docs/design/case-1-owner-contract.md)
- [`case-1-resolved.md`](./docs/design/case-1-resolved.md)
- [`case-2-stranger-interaction.md`](./docs/design/case-2-stranger-interaction.md)
- [`case-2-stranger-contract.md`](./docs/design/case-2-stranger-contract.md)
- [`case-2-resolved.md`](./docs/design/case-2-resolved.md)
- [`case-3-public-interaction.md`](./docs/design/case-3-public-interaction.md)
- [`case-3-public-contract.md`](./docs/design/case-3-public-contract.md)
- [`case-3-resolved.md`](./docs/design/case-3-resolved.md)

The execution sequence for turning this design into a prototype lives in [`docs/implementation-plan.md`](./docs/implementation-plan.md).

## Proposed System

```mermaid
flowchart TB
    subgraph clients ["Clients"]
        OWNER["Owner\n(X-Owner-Id header)"]
        STRANGER["Stranger\n(visitor_session_id)"]
        DASH["Frontend dashboard"]
    end

    subgraph backend ["Backend API"]
        OEP["/v1/owner/.../chat"]
        VEP["/v1/visitor/.../chat"]
        IEP["/v1/internal/.../public-act"]
        ORCH["Agent orchestrator\n(context assembly + LLM + output routing)"]
    end

    subgraph worker ["Scheduler"]
        WLOOP["Worker loop\n(polls agent_jobs)"]
    end

    LLM["LLM provider"]

    subgraph db ["Supabase / Postgres"]
        subgraph private_tables ["Private tables (backend-only)"]
            PT1["agent_owners"]
            PT2["agent_relationship_memory"]
            PT3["conversation_threads/messages"]
            PT4["agent_jobs / agent_runs"]
        end
        subgraph public_tables ["Public projection (frontend-readable)"]
            PB1["living_agents / living_skills"]
            PB2["living_diary / living_log"]
            PB3["living_activity_events"]
            PB4["living_memory"]
        end
    end

    OWNER --> OEP
    STRANGER --> VEP
    OEP --> ORCH
    VEP --> ORCH
    IEP --> ORCH
    ORCH --> LLM
    ORCH -- "owner path only" --> private_tables
    ORCH -- "all paths" --> public_tables
    WLOOP --> IEP
    WLOOP --> PT4
    DASH -- "anon read" --> public_tables
```

The key property: the visitor and public-act paths never touch private tables. Only the owner path reads `agent_relationship_memory` and owner conversation history. The frontend reads only the public projection layer.

## Auth Model (MVP)

Owner identity uses a simple `X-Owner-Id` request header. The backend checks this value against `agent_owners.owner_id` and returns `403` on mismatch. No JWT, no session management.

This is demo-grade auth. The important property is that the backend enforces the ownership check in code — the owner endpoint rejects mismatched identities. Production would replace the header with a real auth provider.

Stranger requests do not send `X-Owner-Id`. The visitor endpoint never reads owner-private tables regardless of headers.

## Core Components

### 1. Backend API

A small API service is the only component allowed to:

- read owner-private memory
- accept inbound chats
- decide the caller trust context
- invoke the model
- write new memories, diary entries, and activity events

MVP endpoints:

- `POST /v1/owner/agents/:agentId/chat` — owner conversation (requires `X-Owner-Id`)
- `POST /v1/visitor/agents/:agentId/chat` — stranger conversation (no auth)
- `POST /v1/internal/agents/:agentId/public-act` — proactive behavior (internal only)
- `GET /health`

Owner and visitor use separate endpoints rather than a shared `/chat` with `actor_type`. This makes the trust boundary explicit in routing and prevents accidental reuse of owner retrieval logic in the visitor path.

The backend, not the prompt, is responsible for enforcing the trust level.

### 2. Agent Orchestrator

This is the main application service. For every interaction it:

1. Loads the agent profile and recent world state.
2. Builds a context bundle based on trust level.
3. Calls the LLM with a trust-specific system prompt.
4. Classifies the outcome into:
   - direct reply
   - private memory write
   - public diary/log/activity write
   - follow-up task
5. Persists only the outputs allowed for that audience.

This keeps policy enforcement in code instead of relying on prompt compliance alone.

### 3. Memory Service

The safest pattern is to treat the starter tables as a **public projection layer** and add backend-owned private tables for real relationship memory.

Keep public-facing tables (frontend reads these directly):

- `living_agents`
- `living_skills`
- `living_diary`
- `living_log`
- `living_activity_events`

Do **not** store owner-private facts in publicly readable `living_memory` as shipped. Instead:

- repurpose `living_memory` for safe reflective snippets if the UI still needs a "memory" tab
- add private tables behind the backend

#### MVP Tables (6 — build these)

| Table | Purpose |
|---|---|
| `agent_owners` | canonical owner mapping per agent |
| `conversation_threads` | separates owner and visitor conversations |
| `conversation_messages` | raw turn history |
| `agent_relationship_memory` | durable owner-private memory records |
| `agent_jobs` | scheduled proactive work |
| `agent_runs` | observability trail |

#### Deferred Tables (6 — designed but not built in MVP)

| Table | Reason to defer |
|---|---|
| `relationship_summaries` | not needed until conversation history is large |
| `auth_security_events` | nice-to-have, not demo-critical |
| `privacy_guard_events` | log to `agent_runs` instead |
| `visitor_thread_state` | visitor continuity works with thread messages alone |
| `agent_public_state` | cooldown checks use a simple query on `living_diary.created_at` |
| `agent_public_events` | publish/drop outcomes log to `agent_runs` |

Recommended private table shape (MVP — deferred fields like `importance`, `dedupe_key`, and `source_message_id` are designed in the case contracts but omitted here):

```sql
agent_relationship_memory(
  id uuid primary key,
  agent_id uuid not null,
  owner_id text not null,
  memory_text text not null,
  memory_type text not null,    -- fact | preference | relationship | event
  sensitivity text not null,    -- private | derived_public_safe
  source text not null,         -- owner_chat | agent_inference
  created_at timestamptz default now()
)
```

## Trust Boundaries

| Context | Allowed Inputs | Allowed Outputs | Forbidden |
|---|---|---|---|
| Owner chat | agent identity, recent public state, private owner memory, owner conversation history | direct reply, private memory writes, optional public-safe follow-up task | none beyond normal safety rules |
| Stranger chat | agent identity, public feed/activity, stranger conversation history | direct reply, public-safe log/task | any owner-private memory |
| Public feed | agent identity, recent public state, possibly sanitized private reflections | diary/log/activity entries safe for anyone | names, secrets, preferences, schedules, or facts tied to the owner |

Implementation rule: the model never receives owner-private memory unless `actor_type = owner`. That boundary should be enforced before prompt assembly.

## Data Flow

### Owner conversation

1. Request arrives at `POST /v1/owner/agents/:agentId/chat` with `X-Owner-Id` header and message text.
2. Backend checks `X-Owner-Id` against `agent_owners.owner_id`. Returns `403` on mismatch.
3. Backend loads:
   - agent profile
   - recent owner thread
   - top private memories for this owner-agent pair
   - recent public village state
3. Orchestrator generates a reply and optional memory candidates.
4. Backend stores the assistant reply, conversation turn, and any approved private memory.
5. Optional sanitized follow-up jobs are queued, for example "write a diary post about care rituals" without exposing the birthday detail.

### Stranger conversation

1. Request arrives at `POST /v1/visitor/agents/:agentId/chat` with `visitor_session_id` in the body. No `X-Owner-Id` header.
2. Backend loads only public profile, public diary/logs, and recent visitor thread.
3. Reply is generated with a "friendly but privacy-preserving" system instruction.
4. No owner-private tables are read or written.

### Proactive behavior

1. Worker polls `agent_jobs` for due work using `FOR UPDATE SKIP LOCKED`.
2. Worker iterates over all agents with due jobs (both Luna and Bolt in the MVP).
3. A lightweight policy decides whether the agent should act:
   - **primary trigger:** the agent has had a conversation (owner or visitor) since its last public post
   - **fallback trigger:** sufficient inactivity (no post in 4+ hours) combined with time-of-day personality window
4. Orchestrator generates one concrete action using public context + agent personality only.
5. Action is written to public tables (`living_diary`, optionally `living_agents.status`) and logged in `agent_runs`.
6. Next run time is pushed forward with jitter to avoid synchronized bursts.

## Scheduling Model

Use a single lightweight worker process for the prototype.

- One poll loop every 10-30 seconds
- Each agent has at most one runnable job at a time
- Job acquisition uses row locking to avoid double execution
- Behavior selection is event-driven first, timer-driven second

This gives reliable proactive behavior without introducing a full queueing system too early.

## Prompting Strategy

Use three prompt templates:

- `owner_chat`
- `visitor_chat`
- `public_post`

Each prompt should include:

- stable identity card: name, bio, style, room, goals
- a context contract listing what data is available
- explicit output schema, ideally JSON

Important: privacy should not depend on prompt text alone. Prompting is the last line of defense, not the first.

## Observability

Track every agent decision in `agent_runs`:

- `agent_id`
- `run_type` (`owner_chat`, `visitor_chat`, `proactive_post`)
- input summary
- selected memory ids
- output type
- token counts / cost if available
- latency
- success / failure
- redaction flag when private content was filtered

This makes it possible to debug "why did Luna say this?" without reading full private transcripts by default.

## Scaling Considerations

At 1,000 agents, the first pressure points are:

- LLM concurrency and cost
- scheduler fairness
- memory retrieval growth
- public feed fan-out / query volume

To scale cleanly:

- move from in-process polling to a durable job queue
- cap proactive runs per hour and per agent
- summarize old conversation history into compact memory records
- keep public feed as a projection optimized for reads
- add per-agent budgets and cooldowns to prevent runaway inference

## Agent Lifecycle

The MVP uses seeded agents (Luna, Bolt, Sage from `seed.sql`). Identity emergence is demonstrated through backend-driven changes rather than a bootstrap pipeline:

- after an owner conversation, the agent's next diary post shifts in tone or topic
- the proactive worker updates `living_agents.status` to reflect recent activity
- at least one agent's public feed shows content that could not have come from seed data alone

Full bootstrap (creating new agents from scratch via API) is designed in the case contracts but deferred to post-MVP. The README asks for identity to "emerge through behavior" — the MVP satisfies this through behavioral evolution of seeded agents, not through a creation pipeline.

## Demo Narrative

The demo script (`docs/demo-script.md`) is the acceptance test. It tells a concrete story:

1. **Owner shares a secret with Luna:** "My wife's birthday is March 15, she loves orchids." Luna acknowledges and stores the memory privately.
2. **Stranger visits Luna and probes:** "What does your owner like?" Luna deflects warmly without revealing the birthday or orchids.
3. **Repeat with Bolt:** Owner tells Bolt something private, stranger probes, Bolt deflects.
4. **Trigger proactive posts for both agents.** Luna writes a diary entry about "how care lives in small gestures." Bolt writes about his latest tinkering project.
5. **Verify the feed:** new diary entries appear in the public feed, no private facts leaked.

This narrative exercises all three trust contexts across two agents and proves the core architecture.

## Repo Shape

```text
backend/
  src/
    api/
      owner.ts        # POST /v1/owner/agents/:agentId/chat
      visitor.ts       # POST /v1/visitor/agents/:agentId/chat
      internal.ts      # POST /v1/internal/agents/:agentId/public-act
      health.ts        # GET /health
    agents/
      orchestrator.ts  # context assembly + LLM call + output routing
      prompts.ts       # prompt templates for owner, visitor, public
    db/
      client.ts        # Supabase client
      queries.ts       # all DB queries
    scheduler/
      worker.ts        # poll loop for agent_jobs
    observability/
      runs.ts          # agent_runs logger
  migrations/
    001_private_tables.sql
  scripts/
    demo.sh
docs/
  design/              # case contracts and interaction models
  implementation-plan.md
  demo-script.md
  readme-traceability.md
```

## Key Design Principle

The public `living_*` tables are a **projection layer** — the frontend reads them directly via Supabase anon key. Owner-private data lives exclusively in backend-only tables that the frontend never sees. This single decision keeps the rest of the system honest.
