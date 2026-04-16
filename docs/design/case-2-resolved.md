# Case 2: Resolved State

This file is the short-form summary of the decisions now considered settled for stranger interaction.

## Resolved Decisions

### Routing and trust

- stranger chat uses a dedicated visitor endpoint
- visitor identity is session-scoped, not person-scoped
- visitor session ids provide continuity only, never privilege

### Context and retrieval

- stranger prompts use only public profile data, public feed context, session state, and explicitly safe abstractions
- stranger prompts never read owner-private tables, owner summaries, or owner chat history
- privacy-sensitive questions are handled through in-character redirects, not raw disclosure

### Retention

- stranger continuity is short-lived
- sessions expire on inactivity and also have a hard maximum age
- the first design target is 24 hours inactivity TTL with a 7 day absolute cap

### Memory and state

- stranger interactions do not create durable long-term visitor profiles
- a harmless nickname may be remembered only within the active session window
- session summaries may exist for continuity, but they are TTL-bound

### Privacy guard

- owner-probing, impersonation attempts, and prompt-injection-style requests trigger a privacy guard path
- privacy-guard triggers are logged in a dedicated lightweight event table
- triggering the guard never expands the retrieval scope

### Write rules

- stranger flows may write visitor thread messages, visitor session state, and observability events
- stranger flows may not write owner-private memory or durable visitor relationship memory

## What Is Still Flexible

These are tuning questions, not architecture blockers:

- exact inactivity TTL after usability testing
- escalation behavior after repeated privacy-guard triggers
- whether stranger interactions should ever create public activity candidates

## Status

Case 2 is now designed well enough to implement without inventing new stranger-memory or privacy behavior mid-build.
