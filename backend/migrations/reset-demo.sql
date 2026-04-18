-- reset-demo.sql
-- Run in Supabase SQL Editor before recording a fresh demo.
-- Removes all backend-generated data while preserving seed data structure.
-- Safe to run multiple times.

-- Remove bootstrapped agents (keeps Luna, Bolt, Sage)
DELETE FROM living_agents WHERE id NOT IN (
  'a1a1a1a1-0000-0000-0000-000000000001',
  'a2a2a2a2-0000-0000-0000-000000000002',
  'a3a3a3a3-0000-0000-0000-000000000003'
);

-- Clear all private tables (backend-generated)
TRUNCATE agent_relationship_memory CASCADE;
TRUNCATE conversation_threads CASCADE;
TRUNCATE conversation_messages CASCADE;
TRUNCATE agent_runs CASCADE;
TRUNCATE agent_jobs CASCADE;

-- Remove worker-generated diary entries (keep seed entries by date)
DELETE FROM living_diary WHERE entry_date > '2026-03-11';

-- Reset agent statuses to seed values
UPDATE living_agents SET status = 'Gazing at constellations' WHERE id = 'a1a1a1a1-0000-0000-0000-000000000001';
UPDATE living_agents SET status = 'Rewiring the coffee machine (again)' WHERE id = 'a2a2a2a2-0000-0000-0000-000000000002';
UPDATE living_agents SET status = 'Pruning thoughts' WHERE id = 'a3a3a3a3-0000-0000-0000-000000000003';

-- Re-seed owner mappings
INSERT INTO agent_owners (agent_id, owner_id) VALUES
  ('a1a1a1a1-0000-0000-0000-000000000001', 'owner-luna-demo'),
  ('a2a2a2a2-0000-0000-0000-000000000002', 'owner-bolt-demo')
ON CONFLICT (agent_id) DO NOTHING;

-- Re-seed proactive jobs (due immediately for demo)
INSERT INTO agent_jobs (agent_id, job_type, run_after) VALUES
  ('a1a1a1a1-0000-0000-0000-000000000001', 'public_act', now() + interval '5 minutes'),
  ('a2a2a2a2-0000-0000-0000-000000000002', 'public_act', now() + interval '5 minutes');
