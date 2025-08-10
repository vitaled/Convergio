-- Database Optimization Script for Convergio
-- ==========================================
-- This script analyzes and optimizes database performance

-- 1. ANALYZE SLOW QUERIES
-- ========================

-- Find slow queries (PostgreSQL)
CREATE OR REPLACE VIEW slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    stddev_time
FROM pg_stat_statements
WHERE mean_time > 100  -- queries averaging over 100ms
ORDER BY mean_time DESC
LIMIT 20;

-- 2. INDEX OPTIMIZATION
-- =====================

-- Agents table indexes
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_workflow_id ON agents(workflow_id);

-- Workflows table indexes
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_user_id ON workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_updated_at ON workflows(updated_at DESC);

-- Audit logs table indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_type_id ON audit_logs(entity_type, entity_id);

-- Costs table indexes
CREATE INDEX IF NOT EXISTS idx_costs_user_id ON costs(user_id);
CREATE INDEX IF NOT EXISTS idx_costs_date ON costs(date DESC);
CREATE INDEX IF NOT EXISTS idx_costs_service ON costs(service);
CREATE INDEX IF NOT EXISTS idx_costs_user_date ON costs(user_id, date DESC);

-- Approval table indexes
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_approvals_user_id ON approvals(user_id);
CREATE INDEX IF NOT EXISTS idx_approvals_workflow_id ON approvals(workflow_id);
CREATE INDEX IF NOT EXISTS idx_approvals_created_at ON approvals(created_at DESC);

-- Messages/Streaming table indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);

-- 3. PARTITIONING FOR LARGE TABLES
-- =================================

-- Partition audit_logs by month
CREATE TABLE IF NOT EXISTS audit_logs_2025_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE IF NOT EXISTS audit_logs_2025_02 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Create future partitions
CREATE OR REPLACE FUNCTION create_monthly_partitions()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    FOR i IN 0..11 LOOP
        start_date := date_trunc('month', CURRENT_DATE + (i || ' months')::interval);
        end_date := start_date + '1 month'::interval;
        partition_name := 'audit_logs_' || to_char(start_date, 'YYYY_MM');
        
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 4. VACUUM AND ANALYZE
-- ======================

-- Update statistics for query planner
ANALYZE agents;
ANALYZE workflows;
ANALYZE users;
ANALYZE audit_logs;
ANALYZE costs;
ANALYZE approvals;
ANALYZE messages;

-- Reclaim storage and update visibility map
VACUUM ANALYZE agents;
VACUUM ANALYZE workflows;
VACUUM ANALYZE users;
VACUUM ANALYZE audit_logs;
VACUUM ANALYZE costs;

-- 5. QUERY OPTIMIZATION EXAMPLES
-- ===============================

-- Optimized query for getting user's active agents
CREATE OR REPLACE VIEW user_active_agents AS
SELECT 
    a.*,
    w.name as workflow_name,
    COUNT(m.id) as message_count
FROM agents a
LEFT JOIN workflows w ON a.workflow_id = w.id
LEFT JOIN messages m ON a.id = m.agent_id
WHERE a.status = 'active'
GROUP BY a.id, w.name;

-- Optimized query for cost aggregation
CREATE OR REPLACE VIEW daily_cost_summary AS
SELECT 
    user_id,
    date,
    SUM(amount) as total_cost,
    COUNT(DISTINCT service) as services_used,
    MAX(amount) as max_single_cost
FROM costs
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY user_id, date;

-- 6. MATERIALIZED VIEWS FOR EXPENSIVE QUERIES
-- ============================================

-- Materialized view for dashboard metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_metrics AS
SELECT 
    COUNT(DISTINCT u.id) as total_users,
    COUNT(DISTINCT a.id) as total_agents,
    COUNT(DISTINCT w.id) as total_workflows,
    SUM(c.amount) as total_cost_today,
    COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END) as active_agents
FROM users u
LEFT JOIN agents a ON u.id = a.user_id
LEFT JOIN workflows w ON u.id = w.user_id
LEFT JOIN costs c ON u.id = c.user_id AND c.date = CURRENT_DATE;

-- Refresh materialized view periodically
CREATE OR REPLACE FUNCTION refresh_dashboard_metrics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_metrics;
END;
$$ LANGUAGE plpgsql;

-- 7. CONNECTION POOLING CONFIGURATION
-- ====================================

-- Recommended PostgreSQL configuration for performance
-- Add these to postgresql.conf:
/*
shared_buffers = 256MB              # 25% of system memory
effective_cache_size = 1GB          # 50-75% of system memory
maintenance_work_mem = 64MB         # For VACUUM, CREATE INDEX
work_mem = 4MB                      # For sorts, hashes
max_connections = 200               # Connection pool size
random_page_cost = 1.1              # For SSD storage
checkpoint_segments = 32            # Increase for write-heavy workloads
checkpoint_completion_target = 0.9  # Spread checkpoint I/O
*/

-- 8. MONITORING QUERIES
-- =====================

-- Monitor table sizes
CREATE OR REPLACE VIEW table_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY size_bytes DESC;

-- Monitor index usage
CREATE OR REPLACE VIEW index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Find unused indexes
CREATE OR REPLACE VIEW unused_indexes AS
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND indexname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;

-- 9. DEADLOCK PREVENTION
-- =======================

-- Set lock timeout to prevent long-running locks
ALTER DATABASE convergio SET lock_timeout = '10s';
ALTER DATABASE convergio SET statement_timeout = '30s';

-- 10. CLEANUP SCRIPTS
-- ===================

-- Remove old audit logs (keep 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM audit_logs 
    WHERE created_at < CURRENT_DATE - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- Remove orphaned records
CREATE OR REPLACE FUNCTION cleanup_orphaned_records()
RETURNS void AS $$
BEGIN
    -- Delete messages without agents
    DELETE FROM messages 
    WHERE agent_id NOT IN (SELECT id FROM agents);
    
    -- Delete costs without users
    DELETE FROM costs 
    WHERE user_id NOT IN (SELECT id FROM users);
    
    -- Delete approvals without workflows
    DELETE FROM approvals 
    WHERE workflow_id NOT IN (SELECT id FROM workflows);
END;
$$ LANGUAGE plpgsql;

-- Schedule periodic maintenance
CREATE OR REPLACE FUNCTION schedule_maintenance()
RETURNS void AS $$
BEGIN
    -- This would be scheduled via pg_cron or external scheduler
    PERFORM cleanup_old_audit_logs();
    PERFORM cleanup_orphaned_records();
    PERFORM refresh_dashboard_metrics();
    VACUUM ANALYZE;
END;
$$ LANGUAGE plpgsql;

-- Final optimization report
SELECT 
    'Database Optimization Complete' as status,
    COUNT(*) as tables_optimized,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') as total_indexes,
    pg_database_size(current_database()) as database_size,
    pg_size_pretty(pg_database_size(current_database())) as database_size_pretty
FROM pg_tables
WHERE schemaname = 'public';