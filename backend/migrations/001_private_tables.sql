-- 001_private_tables.sql
-- Run AFTER setup-database.sql and seed.sql
-- Adds backend-only private tables for trust boundary enforcement
-- =============================================

-- ===========================================
-- TABLE: agent_owners
-- Canonical owner mapping per agent
-- ===========================================
CREATE TABLE IF NOT EXISTS agent_owners (
    agent_id UUID PRIMARY KEY REFERENCES living_agents(id) ON DELETE CASCADE,
    owner_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ===========================================
-- TABLE: conversation_threads
-- Separates owner and visitor conversations
-- ===========================================
CREATE TABLE IF NOT EXISTS conversation_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES living_agents(id) ON DELETE CASCADE,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('owner', 'visitor')),
    actor_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    last_message_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_threads_agent_actor
    ON conversation_threads(agent_id, actor_type, actor_id);

-- ===========================================
-- TABLE: conversation_messages
-- Raw turn history for all conversations
-- ===========================================
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES conversation_threads(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES living_agents(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant')),
    body TEXT NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_thread
    ON conversation_messages(thread_id, created_at);

-- ===========================================
-- TABLE: agent_relationship_memory
-- Durable owner-private memory records
-- ===========================================
CREATE TABLE IF NOT EXISTS agent_relationship_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES living_agents(id) ON DELETE CASCADE,
    owner_id TEXT NOT NULL,
    memory_text TEXT NOT NULL,
    memory_type TEXT NOT NULL CHECK (memory_type IN ('fact', 'preference', 'relationship', 'event')),
    sensitivity TEXT NOT NULL DEFAULT 'private' CHECK (sensitivity IN ('private', 'derived_public_safe')),
    source TEXT NOT NULL DEFAULT 'owner_chat' CHECK (source IN ('owner_chat', 'agent_inference')),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_memory_agent_owner
    ON agent_relationship_memory(agent_id, owner_id);

-- ===========================================
-- TABLE: agent_jobs
-- Scheduled proactive work
-- ===========================================
CREATE TABLE IF NOT EXISTS agent_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES living_agents(id) ON DELETE CASCADE,
    job_type TEXT NOT NULL CHECK (job_type IN ('public_act', 'summarize')),
    run_after TIMESTAMPTZ NOT NULL DEFAULT now(),
    priority INTEGER NOT NULL DEFAULT 3,
    payload JSONB,
    locked_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_jobs_due
    ON agent_jobs(run_after) WHERE completed_at IS NULL AND locked_at IS NULL;

-- ===========================================
-- TABLE: agent_runs
-- Observability trail for every agent decision
-- ===========================================
CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES living_agents(id) ON DELETE CASCADE,
    run_type TEXT NOT NULL CHECK (run_type IN ('owner_chat', 'visitor_chat', 'proactive_post')),
    input_summary TEXT,
    output_type TEXT,
    token_count INTEGER,
    latency_ms INTEGER,
    success BOOLEAN NOT NULL DEFAULT true,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_runs_agent
    ON agent_runs(agent_id, created_at DESC);

-- ===========================================
-- RLS: private tables are backend-only
-- Frontend anon key should NOT read these
-- ===========================================
ALTER TABLE agent_owners ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_relationship_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;

-- Service role (backend) gets full access
DROP POLICY IF EXISTS "service_all" ON agent_owners;
DROP POLICY IF EXISTS "service_all" ON conversation_threads;
DROP POLICY IF EXISTS "service_all" ON conversation_messages;
DROP POLICY IF EXISTS "service_all" ON agent_relationship_memory;
DROP POLICY IF EXISTS "service_all" ON agent_jobs;
DROP POLICY IF EXISTS "service_all" ON agent_runs;
CREATE POLICY "service_all" ON agent_owners FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_all" ON conversation_threads FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_all" ON conversation_messages FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_all" ON agent_relationship_memory FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_all" ON agent_jobs FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_all" ON agent_runs FOR ALL USING (auth.role() = 'service_role');

-- No anon policies = frontend cannot read private tables

-- ===========================================
-- SEED: demo owner mappings
-- ===========================================
INSERT INTO agent_owners (agent_id, owner_id) VALUES
    ('a1a1a1a1-0000-0000-0000-000000000001', 'owner-luna-demo'),
    ('a2a2a2a2-0000-0000-0000-000000000002', 'owner-bolt-demo')
ON CONFLICT (agent_id) DO NOTHING;

-- Seed one public_act job per agent so the worker has work on first run
INSERT INTO agent_jobs (agent_id, job_type, run_after) VALUES
    ('a1a1a1a1-0000-0000-0000-000000000001', 'public_act', now()),
    ('a2a2a2a2-0000-0000-0000-000000000002', 'public_act', now());
