# Case 1: Resolved State

This file is the short-form summary of the decisions now considered settled for owner interaction.

## Resolved Decisions

### Ownership

- each agent has one canonical owner
- owner identity is determined by backend auth, not request payload
- failed owner access on the owner endpoint returns `403 Forbidden`
- failed owner-auth attempts are logged as security events

### Conversation model

- one persistent owner thread per agent-owner pair
- recent messages are loaded directly
- older history is summarized instead of replayed in full

### Memory model

- owner-private memory is stored only in backend-owned tables
- memory is typed, ranked, deduplicated, and sensitivity-labeled
- public-safe abstractions are stored explicitly instead of derived from raw private memory on every read

### Retrieval model

- owner prompt context is assembled from identity, latest summary, recent turns, and top relevant memories
- the first version uses structured retrieval, not embeddings
- unrelated or duplicate memories are excluded from prompt assembly

### Write safety

- not every owner message becomes durable memory
- memory writes go through validation and dedupe checks
- `derived_public_safe` records must pass a projection safety gate before they are stored

### Leak prevention

- stranger and public flows cannot query owner-private tables
- public outputs may only use public data plus explicitly safe abstractions
- raw private facts must never be copied into public diary/log/activity tables

## What Is Still Flexible

These are implementation-tuning questions, not architectural blockers:

- exact summary refresh thresholds
- exact scoring heuristics for memory ranking
- whether public-safe abstractions eventually move into a separate projection table

## Status

Case 1 is now designed well enough to implement without inventing new trust-boundary behavior mid-build.
