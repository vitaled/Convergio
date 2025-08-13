-- Provider pricing indexes and data
CREATE INDEX IF NOT EXISTS idx_provider_pricing_active ON provider_pricing(provider, model, is_active);
CREATE INDEX IF NOT EXISTS idx_provider_pricing_dates ON provider_pricing(effective_from, effective_to);

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

-- Apply trigger to provider_pricing
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

-- Add comment
COMMENT ON VIEW current_pricing IS 'View of currently active pricing for all providers and models';
COMMENT ON MATERIALIZED VIEW cost_analytics_mv IS 'Pre-aggregated cost analytics for performance';