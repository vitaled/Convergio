-- 💰 Convergio Cost Tracking Tables Migration
-- Comprehensive cost tracking for AI model usage across all providers
-- Created: 2025-01-13

-- Create ENUM types
DO $$ BEGIN
    CREATE TYPE provider_type AS ENUM ('openai', 'anthropic', 'perplexity', 'google', 'azure', 'aws_bedrock', 'custom');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE cost_status AS ENUM ('healthy', 'moderate', 'warning', 'exceeded', 'error');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 1. Main cost tracking table
CREATE TABLE IF NOT EXISTS cost_tracking (
    id SERIAL PRIMARY KEY,
    
    -- Session and conversation tracking
    session_id VARCHAR(100) NOT NULL,
    conversation_id VARCHAR(100) NOT NULL,
    turn_id VARCHAR(100),
    
    -- Agent information
    agent_id VARCHAR(100),
    agent_name VARCHAR(200),
    
    -- Provider and model details
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    
    -- Token usage
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    
    -- Cost calculations (high precision)
    input_cost_usd DECIMAL(10, 6) NOT NULL,
    output_cost_usd DECIMAL(10, 6) NOT NULL,
    total_cost_usd DECIMAL(10, 6) NOT NULL,
    
    -- Additional request metadata
    request_type VARCHAR(50), -- chat, completion, embedding, search
    response_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT,
    
    -- Additional metadata JSON for tracking
    request_metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for cost_tracking
CREATE INDEX IF NOT EXISTS idx_cost_tracking_date ON cost_tracking(created_at);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_session_conversation ON cost_tracking(session_id, conversation_id);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_provider_model ON cost_tracking(provider, model);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_agent ON cost_tracking(agent_id);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_turn ON cost_tracking(turn_id);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_total_cost ON cost_tracking(total_cost_usd);

-- 2. Session-level cost aggregation
CREATE TABLE IF NOT EXISTS cost_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL UNIQUE,
    
    -- User information (if available)
    user_id VARCHAR(100),
    
    -- Aggregated costs
    total_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_interactions INTEGER NOT NULL DEFAULT 0,
    
    -- Provider breakdown (JSON)
    provider_breakdown JSONB NOT NULL DEFAULT '{}',
    model_breakdown JSONB NOT NULL DEFAULT '{}',
    agent_breakdown JSONB NOT NULL DEFAULT '{}',
    
    -- Session status
    status VARCHAR(20) NOT NULL DEFAULT 'healthy',
    
    -- Timestamps
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_cost_sessions_session ON cost_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_cost_sessions_user ON cost_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_cost_sessions_dates ON cost_sessions(started_at, ended_at);

-- 3. Daily cost summary for reporting
CREATE TABLE IF NOT EXISTS daily_cost_summary (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    
    -- Total costs
    total_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    total_interactions INTEGER NOT NULL DEFAULT 0,
    total_sessions INTEGER NOT NULL DEFAULT 0,
    
    -- Provider breakdown
    openai_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
    anthropic_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
    perplexity_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
    other_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,
    
    -- Detailed breakdowns (JSON)
    provider_breakdown JSONB NOT NULL DEFAULT '{}',
    model_breakdown JSONB NOT NULL DEFAULT '{}',
    agent_breakdown JSONB NOT NULL DEFAULT '{}',
    hourly_breakdown JSONB NOT NULL DEFAULT '{}',
    
    -- Statistics
    avg_cost_per_interaction DECIMAL(10, 6) NOT NULL DEFAULT 0,
    avg_tokens_per_interaction REAL NOT NULL DEFAULT 0,
    peak_hour_cost DECIMAL(10, 6) NOT NULL DEFAULT 0,
    peak_hour INTEGER,
    
    -- Budget tracking
    daily_budget_usd DECIMAL(10, 6) NOT NULL DEFAULT 50.0,
    budget_utilization_percent REAL NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'healthy',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_cost_summary_date ON daily_cost_summary(date);
CREATE INDEX IF NOT EXISTS idx_daily_cost_summary_status ON daily_cost_summary(status);

-- 4. Provider pricing table
CREATE TABLE IF NOT EXISTS provider_pricing (
    id SERIAL PRIMARY KEY,
    
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    
    -- Pricing per 1K tokens
    input_price_per_1k DECIMAL(10, 6) NOT NULL,
    output_price_per_1k DECIMAL(10, 6) NOT NULL,
    
    -- Additional pricing (for search APIs)
    price_per_request DECIMAL(10, 6),
    
    -- Model capabilities
    max_tokens INTEGER,
    context_window INTEGER,
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_deprecated BOOLEAN NOT NULL DEFAULT false,
    
    -- Effective dates
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    
    -- Metadata
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(provider, model, effective_from)
);

CREATE INDEX IF NOT EXISTS idx_provider_pricing_active ON provider_pricing(provider, model, is_active);
CREATE INDEX IF NOT EXISTS idx_provider_pricing_dates ON provider_pricing(effective_from, effective_to);

-- 5. Cost alerts table
CREATE TABLE IF NOT EXISTS cost_alerts (
    id SERIAL PRIMARY KEY,
    
    -- Alert details
    alert_type VARCHAR(50) NOT NULL, -- daily_limit, session_limit, spike, etc.
    severity VARCHAR(20) NOT NULL, -- info, warning, critical
    
    -- Context
    session_id VARCHAR(100),
    agent_id VARCHAR(100),
    
    -- Alert data
    current_value DECIMAL(10, 6) NOT NULL,
    threshold_value DECIMAL(10, 6) NOT NULL,
    message TEXT NOT NULL,
    
    -- Status
    is_acknowledged BOOLEAN NOT NULL DEFAULT false,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    
    -- Resolution
    is_resolved BOOLEAN NOT NULL DEFAULT false,
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cost_alerts_unresolved ON cost_alerts(is_resolved, severity);
CREATE INDEX IF NOT EXISTS idx_cost_alerts_date ON cost_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_cost_alerts_session ON cost_alerts(session_id);

-- Insert initial pricing data (2025 prices)
INSERT INTO provider_pricing (provider, model, input_price_per_1k, output_price_per_1k, max_tokens, context_window, notes)
VALUES 
    -- OpenAI Models
    ('openai', 'gpt-4o', 0.003, 0.010, 16384, 128000, 'GPT-4o - Latest multimodal model'),
    ('openai', 'gpt-4o-mini', 0.00015, 0.0006, 16384, 128000, 'GPT-4o-mini - Cost efficient small model'),
    ('openai', 'gpt-4-turbo', 0.01, 0.03, 4096, 128000, 'GPT-4 Turbo'),
    ('openai', 'gpt-3.5-turbo', 0.0005, 0.0015, 4096, 16385, 'GPT-3.5 Turbo'),
    ('openai', 'text-embedding-3-small', 0.00002, 0.0, 8191, 8191, 'Small embedding model'),
    ('openai', 'text-embedding-3-large', 0.00013, 0.0, 8191, 8191, 'Large embedding model'),
    
    -- Anthropic Models
    ('anthropic', 'claude-3-5-sonnet-20241022', 0.003, 0.015, 8192, 200000, 'Claude 3.5 Sonnet'),
    ('anthropic', 'claude-3-haiku-20240307', 0.00025, 0.00125, 4096, 200000, 'Claude 3 Haiku - Fast and cost-effective'),
    ('anthropic', 'claude-3-opus-20240229', 0.015, 0.075, 4096, 200000, 'Claude 3 Opus - Most capable'),
    
    -- Perplexity Models (Sonar API)
    ('perplexity', 'sonar', 0.001, 0.001, 4096, 127000, 'Sonar base model'),
    ('perplexity', 'sonar-pro', 0.003, 0.015, 4096, 200000, 'Sonar Pro - Enhanced search'),
    ('perplexity', 'sonar-reasoning', 0.001, 0.005, 4096, 127000, 'Sonar Reasoning'),
    ('perplexity', 'sonar-reasoning-pro', 0.002, 0.008, 4096, 200000, 'Sonar Reasoning Pro'),
    ('perplexity', 'r1-1776', 0.002, 0.008, 4096, 127000, 'R1 1776 model')
ON CONFLICT (provider, model, effective_from) DO NOTHING;

-- Insert search API pricing (per request)
INSERT INTO provider_pricing (provider, model, input_price_per_1k, output_price_per_1k, price_per_request, notes)
VALUES 
    ('perplexity', 'sonar-search', 0.001, 0.001, 0.005, 'Sonar search - $5 per 1000 searches'),
    ('perplexity', 'sonar-deep-research', 0.002, 0.008, 0.005, 'Sonar deep research - $5 per 1000 queries')
ON CONFLICT (provider, model, effective_from) DO NOTHING;

-- Create update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
DROP TRIGGER IF EXISTS update_cost_sessions_updated_at ON cost_sessions;
CREATE TRIGGER update_cost_sessions_updated_at BEFORE UPDATE ON cost_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_daily_cost_summary_updated_at ON daily_cost_summary;
CREATE TRIGGER update_daily_cost_summary_updated_at BEFORE UPDATE ON daily_cost_summary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_provider_pricing_updated_at ON provider_pricing;
CREATE TRIGGER update_provider_pricing_updated_at BEFORE UPDATE ON provider_pricing
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for current pricing
CREATE OR REPLACE VIEW current_pricing AS
SELECT 
    provider,
    model,
    input_price_per_1k,
    output_price_per_1k,
    price_per_request,
    max_tokens,
    context_window,
    notes
FROM provider_pricing
WHERE is_active = true 
    AND is_deprecated = false
    AND effective_from <= NOW()
    AND (effective_to IS NULL OR effective_to > NOW())
ORDER BY provider, model;

-- Create materialized view for cost analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS cost_analytics_mv AS
SELECT 
    DATE_TRUNC('day', created_at) as day,
    provider,
    model,
    agent_id,
    COUNT(*) as interaction_count,
    SUM(total_tokens) as total_tokens,
    SUM(total_cost_usd) as total_cost,
    AVG(total_cost_usd) as avg_cost,
    MAX(total_cost_usd) as max_cost,
    MIN(total_cost_usd) as min_cost,
    AVG(response_time_ms) as avg_response_time
FROM cost_tracking
GROUP BY DATE_TRUNC('day', created_at), provider, model, agent_id;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_cost_analytics_mv_day ON cost_analytics_mv(day);
CREATE INDEX IF NOT EXISTS idx_cost_analytics_mv_provider ON cost_analytics_mv(provider);
CREATE INDEX IF NOT EXISTS idx_cost_analytics_mv_agent ON cost_analytics_mv(agent_id);

-- Grant permissions (adjust as needed)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO convergio_readonly;
-- GRANT INSERT, UPDATE ON cost_tracking, cost_sessions, cost_alerts TO convergio_app;
-- GRANT SELECT ON current_pricing, cost_analytics_mv TO convergio_app;

-- Add comments for documentation
COMMENT ON TABLE cost_tracking IS 'Main table tracking all AI model API calls and their associated costs';
COMMENT ON TABLE cost_sessions IS 'Session-level aggregation of costs for user sessions';
COMMENT ON TABLE daily_cost_summary IS 'Daily aggregated cost data for reporting and analytics';
COMMENT ON TABLE provider_pricing IS 'Current and historical pricing for AI model providers';
COMMENT ON TABLE cost_alerts IS 'Cost threshold alerts and notifications';
COMMENT ON VIEW current_pricing IS 'View of currently active pricing for all providers and models';
COMMENT ON MATERIALIZED VIEW cost_analytics_mv IS 'Pre-aggregated cost analytics for performance';