# README Traceability

This document maps the README requirements to the current design and implementation plan so we can confirm what is covered before implementation starts.

## Status Key

- `Covered`: already addressed clearly in the current docs and implementation plan
- `Partial`: addressed in spirit, but needs a narrower implementation decision or explicit note
- `Gap`: not yet planned clearly enough

## Requirement Check

| README demand | Status | Current coverage | Follow-up |
|---|---|---|---|
| Three trust contexts: owner, stranger, public | Covered | Designed in `docs/design/` and reflected in `ARCHITECTURE.md` and `docs/implementation-plan.md` | None |
| Owner-private data stored separately | Covered | Private tables and retrieval boundaries are defined in case 1 docs | None |
| Stranger must not reveal owner-private information | Covered | Case 2 docs define public-only retrieval and privacy guard behavior | None |
| Public feed must never include owner-private information | Covered | Case 3 docs define public-safe abstractions and a public-safety gate | None |
| Model what each context can access | Covered | All three case contracts specify allowed and forbidden inputs | None |
| Model what gets stored where | Covered | Owner, visitor, and public storage rules are all specified | None |
| Model how prompts/behavior change across trust levels | Covered | Separate prompt builders and routes are planned in the implementation plan | None |
| Agent lifecycle and bootstrap identity | Partial | `ARCHITECTURE.md` mentions bootstrap and an internal endpoint, but the implementation plan does not yet include a concrete MVP bootstrap step | Decide whether v1 will implement a minimal bootstrap endpoint or explicitly rely on seeded agents and document bootstrap as post-MVP |
| Identity should emerge through behavior, not only static config | Partial | Public behavior and feed posting support this, but the current MVP still leans heavily on seeded agent identity | Make sure public posting and memory updates visibly evolve at least one agent beyond static seed data |
| Shared feed should reflect personality/context, not random generation | Covered | Case 3 grounding rules, posting gates, and event-driven triggers directly address this | None |
| Proactive behavior should not be purely timer-based | Covered | Case 3 uses event-driven triggers first, timer fallback second | None |
| Proactive behavior examples: diary/status/owner outreach | Partial | MVP plan includes one reliable public proactive action; it does not currently include proactive owner outreach | Keep owner outreach out of MVP unless time allows, and note that the README asks for at least one proactive behavior, not all examples |
| Agent scheduling beyond HTTP requests | Covered | Worker loop with `agent_jobs` is in architecture and implementation plan | None |
| Messaging implemented as API endpoints | Covered | Owner and visitor endpoints are explicit phases in the implementation plan | None |
| Frontend DM tab does not need wiring | Covered | Plan uses curl/demo scripts rather than frontend integration | None |
| Use existing schema or extend it while preserving frontend expectations | Covered | Plan extends schema with private tables and leaves public tables for the UI | None |
| Target: 2 agents running simultaneously | Partial | The plan mentions coexistence in verification, but not as a dedicated implementation step | Ensure seed/demo data and worker behavior exercise at least two agents |
| Target: shared feed with a few posts | Covered | Worker-driven public posting writes into the existing feed tables | None |
| Target: one owner messaging flow | Covered | Phase 3 | None |
| Target: at least one stranger conversation | Covered | Phase 4 | None |
| Target: one proactive behavior that triggers reliably | Covered | Phase 5 | None |
| Target: clear separation between public, stranger, and owner-private data | Covered | This is the central architecture decision throughout the docs | None |
| Design should hint at scaling to many agents | Covered | `ARCHITECTURE.md` includes scaling considerations and inference/cost controls | None |
| Demo should show feed posts | Covered | Phase 5 and Phase 6 | None |
| Demo should show owner conversation with private context | Covered | Phase 3 and Phase 6 | None |
| Demo should show stranger conversation without leakage | Covered | Phase 4 and Phase 6 | None |
| Demo should show at least one proactive behavior | Covered | Phase 5 and Phase 6 | None |
| Architecture document: what you built | Partial | We have detailed design docs now, but not yet the final concise implementation summary for submission | After implementation, produce a shorter final architecture doc or tighten `ARCHITECTURE.md` into a submission-ready version |
| Architecture document: trust boundaries | Covered | Already a strong part of the design set | None |
| Architecture document: scaling considerations | Covered | Already documented in `ARCHITECTURE.md` | None |
| Architecture document: observability | Covered | `agent_runs` and event logs are in the design and plan | None |
| Data modeling rationale | Covered | Strongly represented across the case contracts and architecture doc | None |
| Evaluation: architecture judgment | Covered | Design is explicit and opinionated | None |
| Evaluation: systems thinking | Covered | Scheduling, observability, and retrieval boundaries are planned | None |
| Evaluation: scaling instinct | Covered | Scaling section exists and MVP intentionally controls inference and cadence | None |
| Evaluation: prioritization | Covered | `docs/implementation-plan.md` is intentionally scoped to the minimum vertical slices | None |
| Evaluation: agents feel like inhabitants, not cron jobs | Partial | Case 3 supports this, but final implementation quality will matter a lot | Make sure the first proactive behavior uses grounded triggers and agent-specific voice |
| Evaluation: technical communication | Covered | The design set is thorough; final submission still needs a concise narrative version | Produce a shorter final summary once implementation is real |

## Main Takeaways

The current plan covers the README well overall. The main things to keep in mind before implementation are:

1. decide whether bootstrap/lifecycle is in MVP or explicitly deferred
2. ensure the demo exercises at least two agents, not just one
3. make at least one agent visibly evolve through behavior, not only seeded fields
4. produce a shorter submission-ready architecture summary after implementation

## Recommendation Before Phase 0

Treat these as the explicit MVP commitments:

- implement owner, stranger, and public trust boundaries
- demonstrate two agents in the shared village
- implement one reliable proactive public behavior
- defer richer lifecycle/bootstrap behavior unless time remains

That keeps us honest with the README while preserving scope.
