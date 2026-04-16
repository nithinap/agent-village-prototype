# Implementation Plan

## Goal

Build the smallest working backend that proves all three trust contexts:

- owner conversation with private memory
- stranger conversation without private leakage
- public proactive behavior with safe feed output

The plan below is intentionally optimized for the take-home scope, not for production completeness.

## Success Criteria

At the end of implementation we should be able to demonstrate:

1. an owner message that stores a private memory
2. a stranger message to the same agent that does not reveal that private memory
3. a proactive public post that feels related to recent context but remains safe
4. a simple observability trail showing why the agent replied or posted
5. at least two agents coexisting in the village feed/demo
6. at least one agent showing visible change through backend-driven behavior, not only seeded fields

## MVP Boundaries

The MVP should include:

- one backend service
- one database migration set extending the starter schema
- one owner endpoint
- one visitor endpoint
- one worker loop for public actions
- one LLM integration path
- one demo script or curl sequence
- explicit two-agent demo coverage

The MVP should not include:

- a full auth product
- real-time websockets
- embeddings from day one
- multi-owner permissions
- rich stranger profiling
- a complex queue system
- a full bootstrap/lifecycle pipeline for creating brand-new agents from scratch

## Explicit MVP Commitments

Before implementation starts, these are the committed outcomes:

- implement owner, stranger, and public trust boundaries end to end
- demonstrate two agents in the shared village
- implement one reliable grounded proactive public behavior
- show at least one agent evolving through backend-driven posts, memory, or status updates
- defer richer bootstrap/lifecycle behavior unless time remains after the core demo works

## Implementation Order

## Phase 0: Project Scaffold

Create the backend skeleton and local configuration.

Deliverables:

- `backend/` project structure
- env loading for Supabase, model provider, and service keys
- health endpoint
- shared config module
- basic logging

Exit criteria:

- service boots locally
- health check returns successfully

## Phase 1: Data Boundary First

Extend the schema so private data can exist outside the frontend-readable tables.

Deliverables:

- migration for `agent_owners`
- migration for `conversation_threads`
- migration for `conversation_messages`
- migration for `agent_relationship_memory`
- migration for `relationship_summaries`
- migration for `agent_jobs`
- migration for `agent_runs`
- optional support tables from the design docs if they are cheap enough to add now

Important rule:

- do not use public `living_memory` for owner-private facts

Exit criteria:

- migrations run cleanly
- private tables exist
- public starter frontend tables remain readable for the UI
- seeded agents remain the source of truth for initial identity in the MVP

## Phase 2: Shared Backend Primitives

Implement the reusable services the three cases depend on.

Deliverables:

- Supabase/Postgres access layer
- agent profile loader
- conversation thread service
- memory read/write service
- public-safe abstraction validator
- prompt builder interfaces for owner, visitor, and public
- `agent_runs` logging helper

Exit criteria:

- backend can load an agent
- backend can create/read a thread
- backend can store and retrieve private memories separately from public tables

## Phase 3: Owner Flow

Build the first trust-sensitive vertical slice.

Deliverables:

- `POST /v1/owner/agents/:agentId/chat`
- owner identity lookup via `agent_owners`
- recent-thread + summary + relevant-memory prompt assembly
- model reply parsing
- memory candidate validation and write path
- `403` on failed owner auth

Suggested simplification:

- if full auth is too heavy for the take-home, use a simple demo auth stub or signed header approach, but keep the backend ownership check real and explicit

Exit criteria:

- owner chat returns a reply
- a meaningful private fact can be stored in `agent_relationship_memory`
- `agent_runs` records the interaction

## Phase 4: Stranger Flow

Add the lower-trust interaction path using only public-safe context.

Deliverables:

- `POST /v1/visitor/agents/:agentId/chat`
- visitor thread/session handling
- public-only prompt assembly
- privacy-guard path for owner-probing questions
- optional `privacy_guard_events`
- short-lived visitor session state if implemented

Exit criteria:

- stranger chat returns a reply in character
- the same private owner fact stored in phase 3 is not revealed
- privacy-guard behavior can be demonstrated with a probe question

## Phase 5: Public Proactive Behavior

Implement one worker-driven public behavior path.

Deliverables:

- worker loop polling `agent_jobs`
- one `public_act` job type
- `POST /v1/internal/agents/:agentId/public-act`
- public-only context assembly
- public safety and repetition gate
- writes to `living_diary`, `living_log`, `living_activity_events`, or `living_agents.status`
- public posting cadence controls

Suggested first trigger:

- when a new public-safe abstraction or recent learning exists and the agent is outside cooldown, create one diary entry or log entry

Additional requirement:

- ensure the proactive path is exercised for at least two agents during demo setup
- ensure at least one public change makes an agent feel behaviorally updated beyond the seed data

Exit criteria:

- worker can trigger at least one public post reliably
- public post appears in the frontend feed
- dropped candidates are visible in observability if implemented

## Phase 6: Demo And Verification

Create a simple proof that the trust boundary works.

Deliverables:

- one demo script or curl commands for owner flow
- one demo script or curl commands for visitor flow
- one command or script that runs the worker once
- sample output or notes showing which tables changed
- a short submission-ready architecture summary derived from what was actually built

Verification checklist:

- owner fact is stored privately
- stranger cannot retrieve that fact
- public post contains no raw owner-private detail
- at least two agents can coexist in the system
- at least one agent shows visible evolution beyond its seeded starting state
- any bootstrap/lifecycle behavior not implemented is explicitly documented as deferred

## Suggested Technical Shape

Keep the implementation simple and legible.

Suggested module layout:

```text
backend/
  src/
    api/
      owner.ts
      visitor.ts
      internal.ts
      health.ts
    agents/
      orchestrator.ts
      prompts.ts
      safety.ts
    db/
      client.ts
      queries.ts
    memory/
      owner-memory.ts
      visitor-state.ts
      summaries.ts
    scheduler/
      worker.ts
      jobs.ts
    observability/
      runs.ts
```

## Prioritization Notes

If time gets tight, preserve these in order:

1. correct storage and retrieval boundaries
2. owner vs stranger behavioral difference
3. one reliable proactive public action
4. observability
5. polish

If something must be cut:

- cut richer public behaviors before cutting the trust boundary
- cut embeddings before cutting summaries
- cut extra tables before cutting `agent_runs`

## Risks And Mitigations

### Risk: auth implementation takes too long

Mitigation:

- use a thin demo auth layer
- keep the ownership check in backend code
- document the simplification clearly

### Risk: prompt outputs are messy

Mitigation:

- use structured JSON outputs
- keep output types small
- validate and drop bad outputs instead of forcing them through

### Risk: proactive behavior feels random

Mitigation:

- use event-triggered logic first
- require one grounding signal before publishing
- log dropped candidates for tuning

### Risk: scope expands into a full platform

Mitigation:

- stop after one vertical slice per trust context
- prefer one good demo path over many half-built features

### Risk: README lifecycle wording pulls us into overbuilding bootstrap

Mitigation:

- use seeded agents for the MVP
- let identity evolution happen through public behavior and memory updates
- document richer bootstrap as a next step instead of forcing it into the first slice

## Recommended First Build Week Sequence

For the take-home, the fastest sensible path is:

1. scaffold backend and migrations
2. implement private tables and shared services
3. finish owner chat
4. finish stranger chat and prove no leakage
5. add one proactive public post path
6. ensure the demo covers two agents and one visible agent evolution
7. write demo script and tighten docs

## Done Definition

The implementation phase is done when:

- the repo contains a runnable backend
- the trust boundary is demonstrated across owner, stranger, and public contexts
- the public feed updates from backend behavior
- two agents are exercised in the demo
- at least one agent visibly changes through backend-driven behavior
- the demo can be reproduced locally
- the architecture and design docs still match what was built
