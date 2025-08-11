-- Create unified memories table with pgvector support
-- This consolidates all memory types into a single table

-- Create enum for memory types
CREATE TYPE memory_type AS ENUM (
    'conversation',
    'context', 
    'knowledge',
    'relationships',
    'preferences',
    'document'
);

-- Create memories table
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_type memory_type NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI embedding dimension
    metadata JSONB DEFAULT '{}',
    
    -- Foreign keys (nullable)
    user_id VARCHAR(255),
    agent_id VARCHAR(255),
    conversation_id VARCHAR(255),
    document_id VARCHAR(255),
    
    -- Scoring and tracking
    importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0 AND importance_score <= 1),
    access_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes for foreign keys
    INDEX idx_memories_user_id (user_id),
    INDEX idx_memories_agent_id (agent_id),
    INDEX idx_memories_conversation_id (conversation_id),
    INDEX idx_memories_document_id (document_id),
    INDEX idx_memories_memory_type (memory_type),
    INDEX idx_memories_created_at (created_at DESC),
    INDEX idx_memories_expires_at (expires_at)
);

-- Create HNSW index for fast vector similarity search
CREATE INDEX IF NOT EXISTS idx_memories_embedding_hnsw
ON memories USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_memories_user_type 
ON memories(user_id, memory_type);

CREATE INDEX IF NOT EXISTS idx_memories_conversation_created
ON memories(conversation_id, created_at DESC);

-- Create function to auto-update last_accessed
CREATE OR REPLACE FUNCTION update_last_accessed()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-updating last_accessed on access
CREATE TRIGGER update_memories_last_accessed
BEFORE UPDATE ON memories
FOR EACH ROW
WHEN (OLD.access_count < NEW.access_count)
EXECUTE FUNCTION update_last_accessed();

-- Create function to clean up expired memories
CREATE OR REPLACE FUNCTION cleanup_expired_memories()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM memories
    WHERE (expires_at IS NOT NULL AND expires_at < NOW())
       OR (created_at < NOW() - INTERVAL '30 days' AND importance_score < 0.5);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON memories TO convergio_user;
GRANT USAGE ON TYPE memory_type TO convergio_user;