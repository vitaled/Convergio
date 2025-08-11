-- Database Optimization Script for Convergio
-- Adds missing indexes, optimizes queries, and improves performance

-- =====================================================
-- 1. Add Missing Indexes for Common Queries
-- =====================================================

-- Index for document_embeddings table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_document_id 
ON document_embeddings(document_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_created_at 
ON document_embeddings(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_chunk_index 
ON document_embeddings(document_id, chunk_index);

-- Composite index for metadata JSONB queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_embeddings_metadata_gin 
ON document_embeddings USING gin(metadata);

-- Index for conversation tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_id 
ON conversations(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_created_at 
ON conversations(created_at DESC);

-- =====================================================
-- 2. Optimize HNSW Indexes for Vector Search
-- =====================================================

-- Drop and recreate HNSW index with better parameters
DROP INDEX IF EXISTS idx_document_embeddings_embedding_hnsw;

CREATE INDEX idx_document_embeddings_embedding_hnsw
ON document_embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 32, ef_construction = 128);

-- Set search parameters for better recall
ALTER DATABASE convergio SET hnsw.ef_search = 100;

-- =====================================================
-- 3. Create Materialized Views for Common Aggregations
-- =====================================================

-- Materialized view for conversation statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS conversation_stats AS
SELECT 
    user_id,
    COUNT(*) as total_conversations,
    AVG(duration_seconds) as avg_duration,
    AVG(turn_count) as avg_turns,
    MAX(created_at) as last_conversation,
    SUM(total_cost) as total_cost_usd
FROM conversations
GROUP BY user_id
WITH DATA;

CREATE UNIQUE INDEX ON conversation_stats(user_id);

-- Refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_conversation_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY conversation_stats;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. Partitioning for Large Tables
-- =====================================================

-- Create partitioned table for document_embeddings by month
CREATE TABLE IF NOT EXISTS document_embeddings_partitioned (
    LIKE document_embeddings INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create partitions for the next 12 months
DO $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    FOR i IN 0..11 LOOP
        start_date := DATE_TRUNC('month', CURRENT_DATE) + (i || ' months')::interval;
        end_date := start_date + '1 month'::interval;
        partition_name := 'document_embeddings_' || TO_CHAR(start_date, 'YYYY_MM');
        
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I 
            PARTITION OF document_embeddings_partitioned
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END LOOP;
END $$;

-- =====================================================
-- 5. Query Optimization Functions
-- =====================================================

-- Function for efficient batch vector search
CREATE OR REPLACE FUNCTION batch_vector_search(
    query_vectors vector[],
    limit_per_query int DEFAULT 5,
    similarity_threshold float DEFAULT 0.7
)
RETURNS TABLE(
    query_index int,
    document_id text,
    content text,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    WITH numbered_queries AS (
        SELECT 
            ROW_NUMBER() OVER () as query_idx,
            unnest(query_vectors) as query_vec
    ),
    ranked_results AS (
        SELECT 
            q.query_idx::int,
            de.document_id,
            de.content,
            1 - (de.embedding <=> q.query_vec) as similarity,
            ROW_NUMBER() OVER (
                PARTITION BY q.query_idx 
                ORDER BY de.embedding <=> q.query_vec
            ) as rank
        FROM numbered_queries q
        CROSS JOIN LATERAL (
            SELECT *
            FROM document_embeddings
            WHERE 1 - (embedding <=> q.query_vec) > similarity_threshold
            ORDER BY embedding <=> q.query_vec
            LIMIT limit_per_query
        ) de
    )
    SELECT 
        query_index,
        document_id,
        content,
        similarity
    FROM ranked_results
    WHERE rank <= limit_per_query
    ORDER BY query_index, rank;
END;
$$ LANGUAGE plpgsql PARALLEL SAFE;

-- =====================================================
-- 6. Connection Pool Configuration
-- =====================================================

-- Optimize connection settings
ALTER DATABASE convergio SET max_connections = 200;
ALTER DATABASE convergio SET shared_buffers = '2GB';
ALTER DATABASE convergio SET effective_cache_size = '6GB';
ALTER DATABASE convergio SET work_mem = '16MB';
ALTER DATABASE convergio SET maintenance_work_mem = '512MB';

-- Optimize for SSD storage
ALTER DATABASE convergio SET random_page_cost = 1.1;
ALTER DATABASE convergio SET effective_io_concurrency = 200;

-- Enable parallel queries
ALTER DATABASE convergio SET max_parallel_workers_per_gather = 4;
ALTER DATABASE convergio SET max_parallel_workers = 8;

-- =====================================================
-- 7. Automatic Maintenance
-- =====================================================

-- Create function for automatic VACUUM and ANALYZE
CREATE OR REPLACE FUNCTION auto_vacuum_analyze()
RETURNS void AS $$
DECLARE
    table_name text;
BEGIN
    FOR table_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('VACUUM ANALYZE %I', table_name);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Schedule daily vacuum (use pg_cron extension if available)
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('daily-vacuum', '0 2 * * *', 'SELECT auto_vacuum_analyze()');

-- =====================================================
-- 8. Statistics and Monitoring
-- =====================================================

-- Create statistics for better query planning
CREATE STATISTICS IF NOT EXISTS document_embeddings_stats 
(dependencies, ndistinct) 
ON document_id, chunk_index 
FROM document_embeddings;

-- Function to get index usage statistics
CREATE OR REPLACE FUNCTION get_index_usage_stats()
RETURNS TABLE(
    table_name text,
    index_name text,
    index_scans bigint,
    index_size text,
    table_size text,
    usage_ratio numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname || '.' || tablename AS table_name,
        indexname AS index_name,
        idx_scan AS index_scans,
        pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
        pg_size_pretty(pg_relation_size(relid)) AS table_size,
        ROUND(100.0 * idx_scan / GREATEST(seq_scan + idx_scan, 1), 2) AS usage_ratio
    FROM pg_stat_user_indexes
    JOIN pg_stat_user_tables USING (schemaname, tablename)
    WHERE schemaname = 'public'
    ORDER BY idx_scan DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 9. Clean Up Old Data
-- =====================================================

-- Function to clean up old embeddings
CREATE OR REPLACE FUNCTION cleanup_old_embeddings(
    days_to_keep int DEFAULT 90
)
RETURNS int AS $$
DECLARE
    deleted_count int;
BEGIN
    DELETE FROM document_embeddings
    WHERE created_at < NOW() - (days_to_keep || ' days')::interval
    AND document_id NOT IN (
        SELECT DISTINCT document_id 
        FROM memories 
        WHERE memory_type = 'document'
    );
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 10. Performance Monitoring Views
-- =====================================================

-- View for slow queries
CREATE OR REPLACE VIEW slow_queries AS
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    stddev_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- queries slower than 100ms
ORDER BY mean_exec_time DESC
LIMIT 20;

-- View for table bloat
CREATE OR REPLACE VIEW table_bloat AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size,
    ROUND(100.0 * pg_relation_size(schemaname||'.'||tablename) / pg_total_relation_size(schemaname||'.'||tablename), 1) AS table_percent
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- =====================================================
-- Final Notes
-- =====================================================
-- Run ANALYZE after applying these changes:
ANALYZE;

-- Check index usage after a few days:
-- SELECT * FROM get_index_usage_stats();

-- Monitor slow queries:
-- SELECT * FROM slow_queries;

-- Schedule regular maintenance:
-- SELECT auto_vacuum_analyze();