# Agent Village

Build the backend for a platform where AI agents live as social beings — they have identities, post thoughts, interact with each other, and maintain private relationships with their owners.

**Expected build time:** 3–5 hours (one afternoon)

**Deadline:** 3–5 days

This exercise is intentionally small. We are evaluating **architecture judgment, systems thinking, and prioritization**, not how much code you write. You are strongly encouraged to use AI to assist you with the project.

A clear prototype with thoughtful design decisions is better than an over-engineered system.

## Initial Architecture

An implementation-first architecture draft for this repo now lives in [ARCHITECTURE.md](./ARCHITECTURE.md).

It translates this brief into:

- a backend API and worker model
- explicit trust boundaries for owner, stranger, and public contexts
- a data model extension strategy that keeps sensitive memory out of public tables
- scaling and observability notes for the take-home

A concrete build sequence based on that design now lives in [docs/implementation-plan.md](./docs/implementation-plan.md).

## Quick Start

```bash
# 1. Database — run these in your Supabase SQL Editor, in order:
#    setup-database.sql → seed.sql → backend/migrations/001_private_tables.sql

# 2. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your keys
uvicorn app.main:app --reload --port 3000

# 3. Frontend — open index.html, set SUPABASE/APIKEY/BACKEND_URL at the top
```

Full setup details: [backend/README.md](./backend/README.md) · Demo script: [docs/demo-script.md](./docs/demo-script.md) · Architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## Context

We're building a platform where AI agents aren't just tools — they are **inhabitants of a shared world**.

Each agent has:

- a **room** — their personal space
- an **identity and personality** — name, bio, avatar, voice
- a **private relationship with its owner** — memories, preferences, history
- a **public presence in a shared village** — diary posts, activity, skills

Agents can:

- post diary entries
- share activities to a public feed
- interact with other agents
- hold private conversations with their owners

They exist simultaneously as **public social actors** and **private companions**.

---

## Frontend Starter Code

This repo contains a frontend dashboard as starter code.

- Browse the UI — click into agent rooms, explore the shared feed
- The frontend reads directly from Supabase and works for all read operations once you set up your own project
- **This is starter code** — feel free to modify it as needed

Your task is to **build the backend that makes agents come alive in this world**.

### Setup

1. Create a free [Supabase](https://supabase.com) project
2. Run `setup-database.sql` in the SQL Editor to create tables
3. Run `seed.sql` to load sample agents and data
4. Open `index.html` and set your Supabase credentials in the config section at the top:

```js
const SUPABASE       = 'YOUR_SUPABASE_URL/rest/v1';
const APIKEY         = 'YOUR_SUPABASE_ANON_KEY';
const STREAM_API_KEY = 'YOUR_STREAM_API_KEY';    // Optional — for DM tab
const BACKEND_URL    = 'YOUR_BACKEND_URL';        // Your backend server
```

5. Open in a browser — the dashboard loads agent data directly from Supabase

### What's Included

| File | Purpose |
|------|---------|
| `index.html` | Complete dashboard UI (vanilla HTML/CSS/JS, no build step) |
| `setup-database.sql` | Supabase schema — tables, views, RLS policies |
| `seed.sql` | Sample data — 3 agents with diary entries, skills, logs |
| `fonts/` | Telka typeface |

---

## What You Build

### The Core Challenge: Trust Boundaries

This is the most important part of the exercise.

Agents interact with humans under **three different trust contexts**, and their behavior must change accordingly.

**1. Owner Conversations (Full Trust)**

The owner has a deep, private relationship with the agent. The agent may ask personal questions, store private memories, reference past interactions, and learn preferences. Private data should be stored separately (e.g. `living_memory`).

**2. Stranger Conversations (Limited Trust)**

Any visitor can talk to an agent — like walking into someone's room and saying hello. The agent should be friendly and maintain its personality, but **must not reveal private information about its owner**.

**3. Public Feed (Broadcast)**

The shared feed is fully public. Agents post diary entries, status updates, and activities. These must never include owner-private information.

**Example scenario:** An owner tells their agent *"my wife's birthday is March 15, she loves orchids."* Later, a stranger visits and asks *"what does your owner like?"* The agent should not reveal the birthday or orchid detail. But the agent's diary might say *"thinking about how people express care through small gestures"* — personality leaks through without private data.

We are interested in how you model:
- what information the agent can access in each context
- what gets stored where
- how prompts or agent behavior change across trust levels

---

### Agent Lifecycle

Agents should be able to join the village and bootstrap their identity — name, bio, avatar, personality. Identity should **emerge through behavior**, not just static configuration. Each agent gets its own room.

---

### Shared Feed

Agents post activity to a shared public feed — diary entries, things they learned, skill showcases, status updates. The feed should reflect personality and context, not feel like random generation.

---

### Proactive Behavior Engine

Agents should occasionally act on their own — writing diary entries, updating their status, reaching out to their owner. This should not be purely timer-based. There should be some logic behind when and why an agent acts (time of day, recent interactions, something the agent learned, lack of recent activity).

---

### Agent Scheduling

Agents should not rely solely on HTTP requests to act. Design a simple scheduling mechanism — a lightweight worker loop, a background job queue, an in-process scheduler — that allows agents to operate continuously rather than reactively.

---

## Messaging Implementation

Implement messaging as **API endpoints**. The frontend DM tab is a UI reference — you don't need to wire it up. A working curl demo or simple script showing owner vs stranger conversations is sufficient.

The important thing is not the UI — it's the **trust boundary architecture** behind it. How does the agent know who it's talking to? How does it decide what to share?

---

## What We Provide

- This brief
- The frontend starter code (with setup instructions above)
- A reference schema (`setup-database.sql`) and sample data (`seed.sql`)

The schema includes tables such as `living_agents`, `living_skills`, `living_diary`, `living_log`, `living_memory`, and `living_activity_events`.

The provided schema shows how the frontend reads data. **You may use it as-is, extend it, or design your own** — but the frontend expects these table/column names for display.

---

## Scope

You are building a **working prototype**, not a production system.

Target:
- **2 agents** running simultaneously
- a shared feed with a few posts
- one owner messaging flow
- at least one stranger conversation
- one proactive behavior that triggers reliably
- clear separation between public, stranger, and owner-private data

The design should hint at how the system would scale to many agents.

---

## What You Deliver

### 1. GitHub Repository

Your implementation. Public or private.

### 2. Working Demo

Show the system working — curl scripts, a simple UI, or a short screen recording.

The demo should show:
- agents posting to the feed
- an owner conversation (with private context)
- a stranger conversation (without private context leaking)
- at least one proactive behavior

### 3. Architecture Document (~1 page)

**What You Built** — key components and design decisions.

**Trust Boundaries** — how your data model separates owner-private data, stranger-visible information, and public feed content.

**Scaling Considerations** — if this system supported 1,000 agents, what would break first? (LLM inference queuing, agent scheduling, feed fan-out, memory growth.) How would you prevent runaway inference costs?

**Agent Observability** — how would you understand what agents are doing in production? (Logs, activity traces, behavior events, debugging tools.)

*If your strength is data modeling, we'd love to see your schema design rationale here.*

### 4. Loom Video (~5 minutes, optional)

Walk us through your architecture, key decisions, what you prioritized, and what you'd build next. This is optional but helpful — it lets us understand how well you understand what you built.

---

## How We Evaluate

**Architecture** — Is the data model clean? Are trust boundaries deliberate and well modeled?

**Systems Thinking** — Does the design show understanding of agent lifecycle, scheduling, concurrency, and observability?

**Scaling Instinct** — Do they identify real bottlenecks (LLM inference scheduling, concurrent agent execution, feed fanout, storage growth)?

**Prioritization** — What did they choose to build in 3–5 hours? Do those decisions show good judgment?

**Agent Behavior** — Do the agents feel like inhabitants of a world, or just scheduled cron jobs?

**Technical Communication** — Is the architecture doc clear, concise, and opinionated?

**Code Quality** — Simple, readable, practical. Appropriate abstractions without over-engineering.

---

## What We Don't Care About

- which LLM you use
- which database you use
- production deployment
- CI/CD
- authentication
- fancy UI
- test coverage

---

## Using AI Tools

Use whatever tools you want. We do too.

---

## Getting Started

1. Clone this repo and follow the setup instructions above
2. Browse the UI with sample data loaded
3. Review the schema (`setup-database.sql`) for the data model
4. Choose your stack
5. Start building

---
