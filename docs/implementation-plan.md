# Implementation Plan

## Goal

Build the smallest working backend that proves all three trust contexts:

- owner conversation with private memory
- stranger conversation without private leakage
- public proactive behavior with safe feed output

The plan below is intentionally optimized for the take-home scope (3-5 hours of implementation), not for production completeness.

## Demo-First Principle

The demo script (`docs/demo-script.md`) defines the acceptance test. Every implementation phase exists to make one part of that demo work. If a feature does not appear in the demo, it does not belong in the MVP build.

## Success Criteria

At the end of implementation we should be able to demonstrate:

1. an owner message that stores a private memory
2. a stranger message to the same agent that does not reveal that private memory
3. a proactive public post that feels related to recent context but remains safe
4. a simple observability trail showing why the agent replied or posted
5. at least two agents exercised equally in the demo
6. at least one agent showing visible change through backend-driven behavior, not only seeded fields

## MVP Boundaries

The MVP includes:

- one backend service (Node.js/TypeScript with Express or Fastify)
- one migration file extending the starter schema with 6 private tables
- one owner chat endpoint
- one visitor chat endpoint
- one internal public-act endpoint
- one worker loop
- one LLM integration path
- one demo script proving the trust boundary

The MVP does not include:

- JWT/session auth (uses `X-Owner-Id` header — see Auth Decision below)
- real-time websockets
- embeddings
- multi-owner permissions
- rich stranger profiling or durable visitor memory
- a complex queue system
- a full bootstrap/lifecycle pipeline

## Auth Decision (Committed)

Owner identity uses a simple `X-Owner-Id` request header. The backend checks this value against `agent_owners.owner_id`. No JWT, no session management, no auth provider.

This is a demo-grade trust boundary. The important thing is that the backend enforces the ownership check in code — the owner endpoint rejects requests where the header does not match the stored owner. Production would replace the header with a real auth provider.

Stranger requests do not send `X-Owner-Id`. The visitor endpoint never reads owner-private tables regardless of what headers are present.

## MVP Tables (Build These)

These 6 tables are required for the demo:

| Table | Purpose |
|---|---|
| `agent_owners` | canonical owner mapping per agent |
| `conversation_threads` | separates owner and visitor conversations |
| `conversation_messages` | raw turn history |
| `agent_relationship_memory` | durable owner-private memory records |
| `agent_jobs` | scheduled proactive work |
| `agent_runs` | observability trail |

## Deferred Tables (Design Only)

These tables are designed in the case contracts but not built in the MVP. They are documented as future work:

| Table | Reason to defer |
|---|---|
| `relationship_summaries` | not needed until conversation history is large |
| `auth_security_events` | nice-to-have observability, not demo-critical |
| `privacy_guard_events` | privacy guard behavior works without a dedicated table — log to `agent_runs` instead |
| `visitor_thread_state` | visitor continuity works with thread messages alone for the MVP |
| `agent_public_state` | cooldown checks can use a simple query on `living_diary.created_at` |
| `agent_public_events` | publish/drop outcomes can log to `agent_runs` |

## Deferred Complexity

These features are designed but not implemented in the MVP:

- memory importance scoring (store all candidates with default importance)
- dedupe_key logic (rely on simple text comparison if needed)
- redaction gate (validate schema only, skip content analysis)
- relationship summaries (load recent messages directly)
- public-safe abstraction pipeline (proactive posts use public context + personality, not derived abstractions)

## Agent Lifecycle Decision

The MVP uses seeded agents. Identity emergence is demonstrated through backend-driven changes:

- after an owner conversation, the agent's next diary post shifts in tone or topic
- the agent's `status` field is updated by the proactive worker
- at least one agent's public feed shows content that could not have come from seed data alone

Full bootstrap (creating new agents from scratch via API) is documented as a next step.

## Implementation Order

### Phase 0: Scaffold (~30 min)

Create the backend skeleton.

Deliverables:

- `backend/` project with TypeScript, Express/Fastify, dotenv
- Supabase client setup (service role key for backend writes)
- `GET /health` endpoint
- basic request logging

Exit criteria: service boots locally, health check returns 200.

### Phase 1: Migrations (~20 min)

Extend the schema with the 6 MVP tables.

Deliverables:

- single migration file: `backend/migrations/001_private_tables.sql`
- seed `agent_owners` rows mapping Luna and Bolt to demo owner ids

Important rules:

- do not use public `living_memory` for owner-private facts
- do not modify existing public tables — they are the frontend projection layer

Exit criteria: migrations run cleanly against Supabase, seeded agents still load in the frontend.

### Phase 2: Owner Chat (~60 min)

Build the first trust-sensitive vertical slice.

Deliverables:

- `POST /v1/owner/agents/:agentId/chat`
- read `X-Owner-Id` header, check against `agent_owners`, return 403 on mismatch
- load/create persistent owner thread
- assemble owner prompt: agent identity + recent messages + relevant memories
- call LLM with structured JSON output schema
- parse reply, store conversation messages, store memory candidates
- log to `agent_runs`

Exit criteria:

- owner chat returns a reply
- a private fact (e.g. "wife's birthday March 15, loves orchids") is stored in `agent_relationship_memory`
- `agent_runs` records the interaction
- request without valid `X-Owner-Id` returns 403

### Phase 3: Stranger Chat (~40 min)

Add the lower-trust interaction path.

Deliverables:

- `POST /v1/visitor/agents/:agentId/chat`
- create/load visitor thread by `visitor_session_id` from request body
- assemble stranger prompt: agent identity + public profile + public feed + visitor thread only
- privacy-aware system instruction (deflect owner-probing questions in character)
- call LLM, store reply in conversation messages
- log to `agent_runs`

Key constraint: this endpoint never queries `agent_owners`, `agent_relationship_memory`, or owner conversation threads. The retrieval boundary is enforced in the query layer, not just the prompt.

Exit criteria:

- stranger chat returns a reply in character
- the private fact stored in Phase 2 is not revealed
- asking "what does your owner like?" produces an in-character deflection

### Phase 4: Proactive Worker (~40 min)

Implement one worker-driven public behavior path.

Deliverables:

- `POST /v1/internal/agents/:agentId/public-act` (internal endpoint, no auth)
- worker loop that polls `agent_jobs` for due `public_act` jobs
- worker iterates over all agents with due jobs (not just one)
- public-only context assembly: agent identity + recent public feed + recent diary
- LLM generates a diary entry or status update grounded in recent context
- simple cooldown: skip if agent posted to `living_diary` in the last 2 hours
- write result to `living_diary` and optionally update `living_agents.status`
- log to `agent_runs` (including skipped/dropped candidates)
- reschedule next job with jitter

Proactive trigger (simplified for MVP):

- if the agent has had any conversation (owner or visitor) since its last public post, generate a diary entry using public context + agent personality
- if no recent conversation, use a time-of-day + personality prompt
- the trigger is conversation-driven first, inactivity-driven second

Two-agent requirement:

- seed `agent_jobs` with one `public_act` job per agent (Luna and Bolt)
- worker processes both agents on each poll cycle
- demo shows both agents producing feed content

Exit criteria:

- worker triggers at least one public post per agent
- posts appear in the frontend feed via `living_diary`
- at least one post reflects recent conversation context without leaking private details

### Phase 5: Demo and Verification (~30 min)

Execute the demo script and verify the trust boundary.

Deliverables:

- run through `docs/demo-script.md` curl sequence
- capture sample outputs
- verify tables changed correctly
- update architecture doc with what was actually built
- document any deferred features

Verification checklist:

- [ ] owner fact is stored in `agent_relationship_memory`, not in `living_memory`
- [ ] stranger cannot retrieve that fact
- [ ] public post contains no raw owner-private detail
- [ ] both Luna and Bolt appear in the demo
- [ ] at least one agent shows visible evolution beyond seed data
- [ ] `agent_runs` contains entries for all three interaction types

## Suggested Module Layout

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
    demo.sh            # executable demo script
```

## Time Budget

| Phase | Estimate | Running total |
|---|---|---|
| Phase 0: Scaffold | 30 min | 0:30 |
| Phase 1: Migrations | 20 min | 0:50 |
| Phase 2: Owner Chat | 60 min | 1:50 |
| Phase 3: Stranger Chat | 40 min | 2:30 |
| Phase 4: Proactive Worker | 40 min | 3:10 |
| Phase 5: Demo + Verification | 30 min | 3:40 |

Buffer: ~80 minutes for debugging, prompt tuning, and doc polish.

## Prioritization Notes

If time gets tight, preserve these in order:

1. correct storage and retrieval boundaries (the core architecture point)
2. owner vs stranger behavioral difference (the demo money shot)
3. one reliable proactive public action per agent
4. observability via `agent_runs`
5. polish and doc tightening

If something must be cut:

- cut richer public behaviors before cutting the trust boundary
- cut the second agent's proactive post before cutting the stranger privacy demo
- cut `agent_runs` logging before cutting the core chat endpoints
- never cut the owner/stranger difference — that is the entire point

## Risks And Mitigations

### Risk: LLM outputs are messy or inconsistent

Mitigation: use structured JSON output schema, keep output types small, validate and drop bad outputs instead of forcing them through.

### Risk: proactive behavior feels random

Mitigation: ground every post in recent conversation or public context. The trigger requires a reason (recent conversation or sufficient inactivity). Log dropped candidates to `agent_runs`.

### Risk: scope expands during implementation

Mitigation: the demo script is the acceptance test. If a feature does not appear in the demo, stop building it. Prefer one good demo path over many half-built features.

### Risk: prompt tuning eats all the time

Mitigation: start with simple prompts, get the plumbing working first. Tune prompts only after the full demo flow works end to end.

## Done Definition

The implementation phase is done when:

- the repo contains a runnable backend
- the demo script in `docs/demo-script.md` can be executed and produces the expected results
- the trust boundary is demonstrated across owner, stranger, and public contexts
- both Luna and Bolt are exercised in the demo
- at least one agent visibly changes through backend-driven behavior
- `agent_runs` contains an observability trail
- the architecture doc reflects what was actually built
