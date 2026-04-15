# Interaction Model

This folder is for design-only decisions. It should define behavior and boundaries before backend code is introduced.

## Interaction Cases

The system has three distinct interaction modes:

1. Agent interacting with the owner
2. Agent interacting with a stranger
3. Agent interacting with the public

These are not prompt variants of the same flow. They are separate trust contexts with different data access rules.

## Shared Design Principle

Trust boundaries are enforced in application code and storage layout first, then reinforced in prompts.

That means:

- retrieval is audience-aware
- storage is audience-aware
- prompts only receive data already approved for that audience

## Case 1: Owner Interaction

Owner interaction is the deepest relationship context.

Characteristics:

- highest trust
- richest memory
- lowest concurrency concern
- strongest need for identity verification

Main design questions:

- how should owner memory be stored and summarized over time?
- how do we authenticate the owner without trusting self-reported claims?
- how do we guarantee private learnings never appear in stranger or public contexts?

Detailed notes live in [case-1-owner-interaction.md](./case-1-owner-interaction.md).

## Case 2: Stranger Interaction

Stranger interaction should feel warm and in-character, but privacy-preserving.

Characteristics:

- no access to owner-private memory
- can use public profile, public feed, and visitor-local conversation history
- should resist both direct questioning and indirect inference attacks

Questions to resolve later:

- what limited memory, if any, should be retained about strangers?
- should stranger chats be persisted long-term or summarized aggressively?
- how should the agent respond when strangers probe for owner details?

## Case 3: Public Interaction

Public interaction covers diary posts, status updates, activity feed entries, and lightweight social actions.

Characteristics:

- content is visible to everyone
- should feel like an extension of the agent's personality
- must never expose owner-private facts

Questions to resolve later:

- what kinds of internal thoughts are safe to project publicly?
- how do we convert private learnings into safe abstractions?
- when should the agent post proactively instead of remaining quiet?

## Design Sequence

We will finalize these cases in order:

1. owner interaction
2. stranger interaction
3. public interaction

That order keeps the hardest privacy boundary grounded first.
