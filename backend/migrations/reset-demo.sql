-- reset-demo.sql
-- Run in Supabase SQL Editor before recording a fresh demo.
-- Wipes everything, then re-run seed.sql and 001_private_tables.sql.
-- Safe to run multiple times.

-- ── Wipe private tables ──
TRUNCATE agent_relationship_memory CASCADE;
TRUNCATE conversation_threads CASCADE;
TRUNCATE conversation_messages CASCADE;
TRUNCATE agent_runs CASCADE;
TRUNCATE agent_jobs CASCADE;
TRUNCATE agent_owners CASCADE;

-- ── Wipe public tables (cascade handles FK deps) ──
TRUNCATE living_agents CASCADE;
TRUNCATE announcements CASCADE;
TRUNCATE living_activity_events CASCADE;

-- After running this, re-run IN THIS ORDER:
--   1. seed.sql                                  (agents must exist first)
--   2. backend/migrations/001_private_tables.sql  (references agents by FK)
