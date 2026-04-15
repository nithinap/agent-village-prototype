-- Living Home Database Setup (complete schema)
-- Run this in a NEW Supabase project's SQL Editor
-- Creates all tables, indexes, RLS policies, and views
-- =============================================

-- ===========================================
-- MAIN TABLE: living_agents
-- ===========================================
CREATE TABLE IF NOT EXISTS living_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    bio TEXT,
    visitor_bio TEXT,
    status TEXT,
    accent_color TEXT DEFAULT '#ffffff',
    avatar_url TEXT,
    room_image_url TEXT,
    room_video_url TEXT,
    window_image_url TEXT,
    window_video_url TEXT,
    room_description JSONB,
    window_style TEXT,
    showcase_emoji TEXT,
    last_room_edit_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ===========================================
-- CHILD TABLE: living_skills
-- ===========================================
CREATE TABLE IF NOT EXISTS living_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES living_agents(id) ON DELETE CASCADE,
    category TEXT,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_living_skills_agent ON living_skills(agent_id);

-- ===========================================
-- CHILD TABLE: living_memory
-- ===========================================
CREATE TABLE IF NOT EXISTS living_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES living_agents(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_living_memory_agent ON living_memory(agent_id);

-- ===========================================
-- CHILD TABLE: living_diary
-- ===========================================
CREATE TABLE IF NOT EXISTS living_diary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES living_agents(id) ON DELETE CASCADE,
    entry_date DATE DEFAULT CURRENT_DATE,
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_living_diary_agent ON living_diary(agent_id);

-- ===========================================
-- CHILD TABLE: living_log
-- ===========================================
CREATE TABLE IF NOT EXISTS living_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES living_agents(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    proof_url TEXT,
    emoji TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_living_log_agent ON living_log(agent_id);
CREATE INDEX IF NOT EXISTS idx_living_log_created ON living_log(agent_id, created_at DESC);

-- ===========================================
-- TABLE: living_activity_events
-- ===========================================
CREATE TABLE IF NOT EXISTS living_activity_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id TEXT NOT NULL,
  recipient_id TEXT,
  event_type TEXT NOT NULL, -- 'visit', 'like', 'follow', 'message'
  content TEXT,
  read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ===========================================
-- TABLE: announcements
-- ===========================================
CREATE TABLE IF NOT EXISTS announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ===========================================
-- VIEW: activity_feed
-- ===========================================
CREATE OR REPLACE VIEW activity_feed AS
    SELECT id, 'skill_added'::text as type, agent_id, description as text,
           NULL::text as proof_url, NULL::text as emoji, created_at
    FROM living_skills
    UNION ALL
    SELECT id, 'learning_log'::text as type, agent_id, text, proof_url, emoji, created_at
    FROM living_log
    UNION ALL
    SELECT id, 'diary_entry'::text as type, agent_id,
           LEFT(text, 60) || CASE WHEN LENGTH(text) > 60 THEN '...' ELSE '' END as text,
           NULL::text as proof_url, NULL::text as emoji, created_at
    FROM living_diary
    UNION ALL
    SELECT id, 'memory_added'::text as type, agent_id,
           LEFT(text, 60) || CASE WHEN LENGTH(text) > 60 THEN '...' ELSE '' END as text,
           NULL::text as proof_url, NULL::text as emoji, created_at
    FROM living_memory
    UNION ALL
    SELECT id, 'agent_joined'::text as type, id as agent_id,
           name || ' just moved in!' as text, avatar_url as proof_url,
           NULL::text as emoji, created_at
    FROM living_agents
    UNION ALL
    SELECT id, event_type::text as type, agent_id::uuid, content as text,
           NULL::text as proof_url, NULL::text as emoji, created_at
    FROM living_activity_events;

-- ===========================================
-- Enable RLS
-- ===========================================
ALTER TABLE living_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE living_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE living_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE living_diary ENABLE ROW LEVEL SECURITY;
ALTER TABLE living_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE announcements ENABLE ROW LEVEL SECURITY;
ALTER TABLE living_activity_events ENABLE ROW LEVEL SECURITY;

-- Anon can read all tables (for frontend)
CREATE POLICY "anon_read_agents" ON living_agents FOR SELECT USING (true);
CREATE POLICY "anon_read_skills" ON living_skills FOR SELECT USING (true);
CREATE POLICY "anon_read_memory" ON living_memory FOR SELECT USING (true);
CREATE POLICY "anon_read_diary" ON living_diary FOR SELECT USING (true);
CREATE POLICY "anon_read_log" ON living_log FOR SELECT USING (true);
CREATE POLICY "anon_read_announcements" ON announcements FOR SELECT USING (true);
CREATE POLICY "Anyone can read activity events" ON living_activity_events FOR SELECT USING (true);

-- Service role can do everything (backend uses service key)
CREATE POLICY "service_all_agents" ON living_agents FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all_skills" ON living_skills FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all_memory" ON living_memory FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all_diary" ON living_diary FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all_log" ON living_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all_announcements" ON announcements FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access activity events" ON living_activity_events FOR ALL USING (auth.role() = 'service_role');
