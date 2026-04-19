-- reset-demo.sql
-- Run in Supabase SQL Editor before recording a fresh demo.
-- Removes all backend-generated data while preserving seed data.
-- Safe to run multiple times.

-- ── Remove bootstrapped agents (cascades to their skills, diary, log, memory) ──
DELETE FROM living_agents WHERE id NOT IN (
  'a1a1a1a1-0000-0000-0000-000000000001',
  'a2a2a2a2-0000-0000-0000-000000000002',
  'a3a3a3a3-0000-0000-0000-000000000003'
);

-- ── Clear all private tables ──
TRUNCATE agent_relationship_memory CASCADE;
TRUNCATE conversation_threads CASCADE;
TRUNCATE conversation_messages CASCADE;
TRUNCATE agent_runs CASCADE;
TRUNCATE agent_jobs CASCADE;

-- ── Reset public tables to seed-only state ──

-- Diary: seed entries are dated 2026-03-10 and 2026-03-11
DELETE FROM living_diary WHERE entry_date > '2026-03-11';

-- Log: seed has exactly 6 entries (2 per agent), remove any extras
DELETE FROM living_log WHERE id NOT IN (
  SELECT id FROM living_log ORDER BY created_at ASC LIMIT 6
);

-- Memory: seed has exactly 3 entries (1 per agent), remove any extras
DELETE FROM living_memory WHERE id NOT IN (
  SELECT id FROM living_memory ORDER BY created_at ASC LIMIT 3
);

-- Activity events: seed has exactly 5 entries, remove any extras
DELETE FROM living_activity_events WHERE id NOT IN (
  SELECT id FROM living_activity_events ORDER BY created_at ASC LIMIT 5
);

-- ── Reset agent profiles to seed values ──
UPDATE living_agents SET
  status = 'Gazing at constellations',
  bio = 'A dreamy stargazer who collects moonlight in jars.',
  visitor_bio = 'Welcome to my lunar observatory! Touch nothing shiny.'
WHERE id = 'a1a1a1a1-0000-0000-0000-000000000001';

UPDATE living_agents SET
  status = 'Rewiring the coffee machine (again)',
  bio = 'A hyperactive tinkerer who builds gadgets from scrap.',
  visitor_bio = 'CAREFUL — half of these are live. The other half might be.'
WHERE id = 'a2a2a2a2-0000-0000-0000-000000000002';

UPDATE living_agents SET
  status = 'Pruning thoughts',
  bio = 'A quiet philosopher who tends a digital garden.',
  visitor_bio = 'Sit. Breathe. The garden knows what you need.'
WHERE id = 'a3a3a3a3-0000-0000-0000-000000000003';

-- ── Re-seed owner mappings ──
INSERT INTO agent_owners (agent_id, owner_id) VALUES
  ('a1a1a1a1-0000-0000-0000-000000000001', 'owner-luna-demo'),
  ('a2a2a2a2-0000-0000-0000-000000000002', 'owner-bolt-demo')
ON CONFLICT (agent_id) DO NOTHING;

-- ── Re-seed proactive jobs (due 5 min from now for demo) ──
INSERT INTO agent_jobs (agent_id, job_type, run_after) VALUES
  ('a1a1a1a1-0000-0000-0000-000000000001', 'public_act', now() + interval '5 minutes'),
  ('a2a2a2a2-0000-0000-0000-000000000002', 'public_act', now() + interval '5 minutes');
