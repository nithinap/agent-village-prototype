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
| Agent lifecycle and bootstrap identity | Covered | MVP uses seeded agents. Identity emergence is demonstrated through backend-driven diary posts, status updates, and memory-influenced behavior. Full bootstrap is explicitly deferred. See Agent Lifecycle section in `ARCHITECTURE.md`. | None |
| Identity should emerge through behavior, not only static config | Covered | Implementation plan Phase 4 requires at least one agent to show visible change beyond seed data through proactive posts grounded in recent conversation context. | None |
| Shared feed should reflect personality/context, not random generation | Covered | Case 3 grounding rules, posting gates, and event-driven triggers directly address this | None |
| Proactive behavior should not be purely timer-based | Covered | Proactive trigger is conversation-driven first (post if agent had a recent conversation), inactivity-driven second. See implementation plan Phase 4. | None |
| Proactive behavior examples: diary/status/owner outreach | Covered | MVP implements diary entries and status updates. Owner outreach is documented as post-MVP. The README asks for "at least one proactive behavior" — MVP delivers two (diary + status). | None |
| Agent scheduling beyond HTTP requests | Covered | Worker loop with `agent_jobs` is in architecture and implementation plan | None |
| Messaging implemented as API endpoints | Covered | Owner and visitor endpoints are explicit phases in the implementation plan | None |
| Frontend DM tab does not need wiring | Covered | Plan uses curl/demo scripts rather than frontend integration | None |
| Use existing schema or extend it while preserving frontend expectations | Covered | Plan extends schema with private tables and leaves public tables for the UI | None |
| Target: 2 agents running simultaneously | Covered | Implementation plan Phase 4 explicitly seeds `agent_jobs` for both Luna and Bolt, worker iterates over all agents, demo script exercises both. | None |
| Target: shared feed with a few posts | Covered | Worker-driven public posting writes into the existing feed tables | None |
| Target: one owner messaging flow | Covered | Phase 2 | None |
| Target: at least one stranger conversation | Covered | Phase 3 | None |
| Target: one proactive behavior that triggers reliably | Covered | Phase 4 | None |
| Target: clear separation between public, stranger, and owner-private data | Covered | This is the central architecture decision throughout the docs | None |
| Design should hint at scaling to many agents | Covered | `ARCHITECTURE.md` includes scaling considerations and inference/cost controls | None |
| Demo should show feed posts | Covered | Phase 4 and Phase 5, plus `docs/demo-script.md` | None |
| Demo should show owner conversation with private context | Covered | Phase 2 and `docs/demo-script.md` | None |
| Demo should show stranger conversation without leakage | Covered | Phase 3 and `docs/demo-script.md` | None |
| Demo should show at least one proactive behavior | Covered | Phase 4 and `docs/demo-script.md` | None |
| Architecture document: what you built | Covered | `ARCHITECTURE.md` includes Demo Narrative section and will be tightened after implementation | None |
| Architecture document: trust boundaries | Covered | Already a strong part of the design set | None |
| Architecture document: scaling considerations | Covered | Already documented in `ARCHITECTURE.md` | None |
| Architecture document: observability | Covered | `agent_runs` and event logs are in the design and plan | None |
| Data modeling rationale | Covered | Strongly represented across the case contracts and architecture doc | None |
| Evaluation: architecture judgment | Covered | Design is explicit and opinionated | None |
| Evaluation: systems thinking | Covered | Scheduling, observability, and retrieval boundaries are planned | None |
| Evaluation: scaling instinct | Covered | Scaling section exists and MVP intentionally controls inference and cadence | None |
| Evaluation: prioritization | Covered | `docs/implementation-plan.md` is intentionally scoped with time budget and explicit deferred-complexity list | None |
| Evaluation: agents feel like inhabitants, not cron jobs | Covered | Proactive trigger is conversation-driven, posts are grounded in recent context, agent personality shapes output | None |
| Evaluation: technical communication | Covered | The design set is thorough; `ARCHITECTURE.md` includes a demo narrative for submission readiness | None |

## Main Takeaways

All README requirements are now covered. The previously Partial items have been resolved:

1. **Agent lifecycle/bootstrap:** MVP uses seeded agents with identity emergence through backend-driven behavior. Full bootstrap is explicitly deferred.
2. **Two-agent coverage:** Implementation plan Phase 4 seeds jobs for both Luna and Bolt, worker iterates over all agents, demo script exercises both.
3. **Agent evolution beyond seed data:** At least one agent must show visible change through proactive posts grounded in recent conversation context.
4. **Architecture doc submission readiness:** `ARCHITECTURE.md` now includes Auth Model, Demo Narrative, and Agent Lifecycle sections.
5. **Agents feeling like inhabitants:** Proactive trigger is conversation-driven, posts are grounded in context, agent personality shapes output.

## Decisions Made Since Initial Traceability

| Decision | Resolution |
|---|---|
| Auth approach | `X-Owner-Id` header checked against `agent_owners.owner_id`. No JWT. |
| Bootstrap/lifecycle | Deferred. Seeded agents + behavioral evolution. |
| Proactive trigger | Conversation-driven first, inactivity-driven second. |
| Two-agent demo | Both Luna and Bolt seeded with `agent_jobs`, both exercised in demo script. |
| MVP table scope | 6 tables built, 6 tables deferred. See implementation plan. |
| Owner outreach | Deferred. MVP proactive behavior is public posting only. |
