-- ====================================================================
-- Personal AI Advisor & Memory Vault — Supabase Database Schema
-- Modeled after Google AI Studio
-- ====================================================================

-- 1. Enable pgcrypto for UUID generation if not already active
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ====================================================================
-- 2. TABLE: advisors
-- ====================================================================
CREATE TABLE IF NOT EXISTS advisors (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT '🤖',
    color TEXT NOT NULL DEFAULT '#4E80EE',
    system_instructions TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ====================================================================
-- 3. TABLE: memory_cells
-- Scope is 'main' for Shared Memory, or advisor.id for Isolated Memory
-- ====================================================================
CREATE TABLE IF NOT EXISTS memory_cells (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    scope TEXT NOT NULL DEFAULT 'main',
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    cell_order INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_memory_cells_scope_order ON memory_cells(scope, cell_order);
CREATE INDEX IF NOT EXISTS idx_memory_cells_expires_at ON memory_cells(expires_at) WHERE expires_at IS NOT NULL;

-- ====================================================================
-- 4. TABLE: chat_threads
-- Scope is 'main' for Main Chat or advisor.id for dedicated Advisor Chat
-- ====================================================================
CREATE TABLE IF NOT EXISTS chat_threads (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    scope TEXT NOT NULL DEFAULT 'main',
    title TEXT NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_chat_threads_scope_updated ON chat_threads(scope, updated_at DESC);

-- ====================================================================
-- 5. TABLE: chat_messages
-- Messages belonging to a thread, with cascade delete
-- ====================================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    thread_id TEXT NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    thinking_process TEXT NULL,
    search_html TEXT NULL,
    sources_json JSONB NULL,
    attached_file_name TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_thread_created ON chat_messages(thread_id, created_at ASC);

-- ====================================================================
-- 6. TABLE: app_settings
-- Single-row configuration store for model selection & tool toggles
-- ====================================================================
CREATE TABLE IF NOT EXISTS app_settings (
    id TEXT PRIMARY KEY DEFAULT 'default',
    selected_model TEXT NOT NULL DEFAULT 'gemini-4-hydrogen',
    enable_google_search BOOLEAN NOT NULL DEFAULT true,
    enable_url_context BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ====================================================================
-- 7. Row-Level Security (RLS) Setup
-- Enable RLS and grant full access to 'anon' and 'authenticated' roles
-- for seamless Streamlit Community Cloud operations.
-- ====================================================================
ALTER TABLE advisors ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_cells ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;

-- Advisors policies
DROP POLICY IF EXISTS "Allow public all on advisors" ON advisors;
CREATE POLICY "Allow public all on advisors" ON advisors FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

-- Memory cells policies
DROP POLICY IF EXISTS "Allow public all on memory_cells" ON memory_cells;
CREATE POLICY "Allow public all on memory_cells" ON memory_cells FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

-- Chat threads policies
DROP POLICY IF EXISTS "Allow public all on chat_threads" ON chat_threads;
CREATE POLICY "Allow public all on chat_threads" ON chat_threads FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

-- Chat messages policies
DROP POLICY IF EXISTS "Allow public all on chat_messages" ON chat_messages;
CREATE POLICY "Allow public all on chat_messages" ON chat_messages FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

-- App settings policies
DROP POLICY IF EXISTS "Allow public all on app_settings" ON app_settings;
CREATE POLICY "Allow public all on app_settings" ON app_settings FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

-- ====================================================================
-- 8. Seed Initial Default Data (Safe upsert)
-- ====================================================================
INSERT INTO app_settings (id, selected_model, enable_google_search, enable_url_context)
VALUES ('default', 'gemini-4-hydrogen', true, true)
ON CONFLICT (id) DO NOTHING;

-- Seed Sample Advisors
INSERT INTO advisors (id, name, icon, color, system_instructions)
VALUES 
    ('adv-academic', 'University Advisor', '🎓', '#4E80EE', 'You are my rigorous, supportive academic advisor. You prioritize conceptual mastery, precise problem-solving steps, structured unit reviews, and strategic study scheduling.'),
    ('adv-architect', 'Tech Architect', '💻', '#34A853', 'You are my senior cloud systems architect and software engineering advisor. You emphasize clean code, distributed architecture, scalability, security, and pragmatic trade-offs.')
ON CONFLICT (id) DO NOTHING;

-- Seed Sample Main Memory (Shared)
INSERT INTO memory_cells (id, scope, title, content, cell_order, expires_at)
VALUES 
    ('mem-main-1', 'main', '🎯 Core Objective 2026', 'Focusing on advanced distributed computing, AI agents, and maintaining high academic excellence. Prefer concise, high-signal explanations with code examples.', 0, NULL),
    ('mem-main-2', 'main', '⚙️ Engineering Standards', 'Always adhere to clean architecture, explicit type hinting in Python, comprehensive documentation, and modern UI best practices.', 1, NULL)
ON CONFLICT (id) DO NOTHING;

-- Seed Sample Advisor Memory (Academic Advisor)
INSERT INTO memory_cells (id, scope, title, content, cell_order, expires_at)
VALUES 
    ('mem-adv-1', 'adv-academic', '📚 Semester Curriculum & Milestones', 'Current focus: Advanced Database Systems (Supabase/PostgreSQL internals), Machine Learning Systems, and Distributed Consensus algorithms.', 0, NULL)
ON CONFLICT (id) DO NOTHING;

-- ====================================================================
-- Helpful comment:
-- To execute this in Supabase:
-- 1. Go to your Supabase Project Dashboard -> SQL Editor
-- 2. Click "New Query", paste this entire script, and click "Run"
-- ====================================================================
