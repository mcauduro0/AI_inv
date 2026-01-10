-- =============================================================================
-- Investment Agent System - Database Schema
-- =============================================================================
-- Run: psql -U postgres -d investment_agents -f 001_create_schema.sql
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- USERS & AUTHENTICATION
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);

-- =============================================================================
-- RESEARCH PROJECTS
-- =============================================================================

CREATE TYPE research_status AS ENUM (
    'idea',
    'screening',
    'deep_dive',
    'thesis_development',
    'monitoring',
    'closed'
);

CREATE TYPE conviction_level AS ENUM (
    'low',
    'medium',
    'high',
    'very_high'
);

CREATE TABLE IF NOT EXISTS research_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    status research_status DEFAULT 'idea',
    research_type VARCHAR(50) DEFAULT 'standard',
    
    -- Thesis fields
    thesis_summary TEXT,
    bull_case TEXT,
    bear_case TEXT,
    key_catalysts JSONB DEFAULT '[]',
    key_risks JSONB DEFAULT '[]',
    
    -- Valuation
    target_price DECIMAL(15, 4),
    current_price DECIMAL(15, 4),
    conviction_level conviction_level,
    
    -- Metadata
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_research_user ON research_projects(user_id);
CREATE INDEX idx_research_ticker ON research_projects(ticker);
CREATE INDEX idx_research_status ON research_projects(status);

-- =============================================================================
-- RESEARCH NOTES
-- =============================================================================

CREATE TYPE note_type AS ENUM (
    'general',
    'financial',
    'competitive',
    'management',
    'risk',
    'catalyst',
    'valuation',
    'meeting'
);

CREATE TABLE IF NOT EXISTS research_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    note_type note_type DEFAULT 'general',
    source_url VARCHAR(1024),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notes_project ON research_notes(project_id);
CREATE INDEX idx_notes_type ON research_notes(note_type);

-- =============================================================================
-- WORKFLOWS
-- =============================================================================

CREATE TYPE workflow_status AS ENUM (
    'active',
    'paused',
    'completed',
    'failed',
    'cancelled'
);

CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_type VARCHAR(100) NOT NULL,
    config JSONB DEFAULT '{}',
    schedule VARCHAR(100),
    status workflow_status DEFAULT 'active',
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_workflows_user ON workflows(user_id);
CREATE INDEX idx_workflows_type ON workflows(workflow_type);
CREATE INDEX idx_workflows_status ON workflows(status);

CREATE TABLE IF NOT EXISTS workflow_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    status workflow_status DEFAULT 'active',
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER
);

CREATE INDEX idx_workflow_runs_workflow ON workflow_runs(workflow_id);
CREATE INDEX idx_workflow_runs_status ON workflow_runs(status);

-- =============================================================================
-- AGENT TASKS
-- =============================================================================

CREATE TYPE task_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE task_priority AS ENUM (
    'low',
    'normal',
    'high',
    'critical'
);

CREATE TABLE IF NOT EXISTS agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_run_id UUID REFERENCES workflow_runs(id) ON DELETE SET NULL,
    project_id UUID REFERENCES research_projects(id) ON DELETE SET NULL,
    
    agent_type VARCHAR(100) NOT NULL,
    prompt_name VARCHAR(255) NOT NULL,
    input_data JSONB NOT NULL DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    
    status task_status DEFAULT 'pending',
    priority task_priority DEFAULT 'normal',
    error_message TEXT,
    
    -- Metrics
    tokens_used INTEGER DEFAULT 0,
    model_used VARCHAR(100),
    execution_time_seconds DECIMAL(10, 3),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_tasks_agent ON agent_tasks(agent_type);
CREATE INDEX idx_tasks_status ON agent_tasks(status);
CREATE INDEX idx_tasks_workflow ON agent_tasks(workflow_run_id);
CREATE INDEX idx_tasks_project ON agent_tasks(project_id);

-- =============================================================================
-- SCREENER RESULTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS screener_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    screener_name VARCHAR(255) NOT NULL,
    screener_config JSONB NOT NULL DEFAULT '{}',
    
    ticker VARCHAR(20) NOT NULL,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    
    overall_score DECIMAL(5, 2),
    scores_breakdown JSONB DEFAULT '{}',
    ai_summary TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_screener_name ON screener_results(screener_name);
CREATE INDEX idx_screener_ticker ON screener_results(ticker);
CREATE INDEX idx_screener_score ON screener_results(overall_score DESC);

-- =============================================================================
-- INVESTMENT IDEAS
-- =============================================================================

CREATE TYPE idea_source AS ENUM (
    'thematic',
    'newsletter',
    'sec_filing',
    'social_media',
    'institutional',
    'insider',
    'screener',
    'manual'
);

CREATE TABLE IF NOT EXISTS investment_ideas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    ticker VARCHAR(20),
    company_name VARCHAR(255),
    theme VARCHAR(255),
    source idea_source NOT NULL,
    source_details JSONB DEFAULT '{}',
    
    summary TEXT,
    thesis TEXT,
    
    initial_score DECIMAL(5, 2),
    current_score DECIMAL(5, 2),
    
    status VARCHAR(50) DEFAULT 'new',
    promoted_to_project_id UUID REFERENCES research_projects(id) ON DELETE SET NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ideas_user ON investment_ideas(user_id);
CREATE INDEX idx_ideas_ticker ON investment_ideas(ticker);
CREATE INDEX idx_ideas_source ON investment_ideas(source);
CREATE INDEX idx_ideas_status ON investment_ideas(status);

-- =============================================================================
-- PROMPT LIBRARY
-- =============================================================================

CREATE TABLE IF NOT EXISTS prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    
    description TEXT,
    prompt_template TEXT NOT NULL,
    system_prompt TEXT,
    
    input_schema JSONB DEFAULT '{}',
    output_schema JSONB DEFAULT '{}',
    
    model_preference VARCHAR(100),
    temperature DECIMAL(3, 2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4096,
    
    tags JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_prompts_category ON prompts(category);
CREATE INDEX idx_prompts_name ON prompts(name);

-- =============================================================================
-- EMBEDDINGS CACHE
-- =============================================================================

CREATE TABLE IF NOT EXISTS embeddings_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_hash VARCHAR(64) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    reference_id UUID,
    
    embedding VECTOR(1536),  -- OpenAI ada-002 dimension
    model_used VARCHAR(100) NOT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_embeddings_hash ON embeddings_cache(content_hash);
CREATE INDEX idx_embeddings_type ON embeddings_cache(content_type);

-- =============================================================================
-- AUDIT LOG
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);

-- =============================================================================
-- FUNCTIONS & TRIGGERS
-- =============================================================================

-- Updated at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_projects_updated_at
    BEFORE UPDATE ON research_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_notes_updated_at
    BEFORE UPDATE ON research_notes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at
    BEFORE UPDATE ON workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_investment_ideas_updated_at
    BEFORE UPDATE ON investment_ideas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompts_updated_at
    BEFORE UPDATE ON prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Create default admin user (password: admin123)
INSERT INTO users (email, hashed_password, full_name, is_superuser)
VALUES (
    'admin@investment-agents.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.4Iu8Ij5FQJyKHC',
    'System Administrator',
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- =============================================================================
-- GRANT PERMISSIONS
-- =============================================================================

-- Grant all privileges to the application user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO investment_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO investment_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO investment_user;
