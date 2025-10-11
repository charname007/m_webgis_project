-- SQL script for setting up V15 database persistence
-- Please ensure the `pgvector` extension is enabled in your PostgreSQL database:
-- CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Table for Memory Manager's Knowledge Base
CREATE TABLE IF NOT EXISTS memory_knowledge_base (
    id SERIAL PRIMARY KEY,
    query_embedding vector(1536), -- Assumes a 1536-dimension embedding model. Adjust if necessary.
    query_text TEXT NOT NULL UNIQUE, -- Ensures we don't store duplicate questions.
    sql_query TEXT NOT NULL, 
    result_summary JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ,
    access_count INT DEFAULT 0
);

-- Create an index for efficient vector similarity search
-- This is crucial for performance when the knowledge base grows.
CREATE INDEX IF NOT EXISTS idx_query_embedding 
ON memory_knowledge_base 
USING ivfflat (query_embedding vector_l2_ops) WITH (lists = 100);

COMMENT ON TABLE memory_knowledge_base IS 'Stores learned query patterns and their successful SQL translations for semantic caching.';
COMMENT ON COLUMN memory_knowledge_base.query_embedding IS 'Embedding vector of the user query text for similarity search.';


-- 2. Table for Checkpoint Manager's Conversation States
CREATE TABLE IF NOT EXISTS conversation_checkpoints (
    checkpoint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(255) NOT NULL,
    state_snapshot JSONB NOT NULL, -- Stores the full AgentState JSON object.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    step_number INT,
    is_latest BOOLEAN DEFAULT TRUE
);

-- Create an index for quickly finding checkpoints for a given conversation
CREATE INDEX IF NOT EXISTS idx_conversation_id_latest ON conversation_checkpoints (conversation_id, is_latest);

-- Logic to ensure only one checkpoint is the 'latest' per conversation.
-- This can be handled by application logic, but a database trigger is more robust.
CREATE OR REPLACE FUNCTION fn_ensure_single_latest_checkpoint() 
RETURNS TRIGGER AS $$
BEGIN
    -- Set any other 'latest' checkpoints for this conversation_id to false
    UPDATE conversation_checkpoints
    SET is_latest = FALSE
    WHERE conversation_id = NEW.conversation_id AND is_latest = TRUE;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop the trigger if it exists, to avoid errors on re-running the script
DROP TRIGGER IF EXISTS trg_ensure_single_latest ON conversation_checkpoints;

CREATE TRIGGER trg_ensure_single_latest
BEFORE INSERT ON conversation_checkpoints
FOR EACH ROW
WHEN (NEW.is_latest = TRUE)
EXECUTE FUNCTION fn_ensure_single_latest_checkpoint();

COMMENT ON TABLE conversation_checkpoints IS 'Saves snapshots of agent states for conversation persistence and recovery.';
COMMENT ON COLUMN conversation_checkpoints.state_snapshot IS 'A complete JSON dump of the AgentState at a specific point in time.';


-- Initial confirmation message
SELECT 'V15 database setup script loaded. Please execute in your PostgreSQL database.' AS script_status;
