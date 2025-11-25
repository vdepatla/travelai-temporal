-- Initial database setup for LangGraph Travel Agent
-- This file is automatically executed when the PostgreSQL container starts

-- Ensure the database exists (though it should be created by environment variables)
SELECT 'CREATE DATABASE langgraph_checkpoints' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'langgraph_checkpoints');

-- Create extension for better performance (optional)
\c langgraph_checkpoints;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- The LangGraph checkpointer will automatically create these tables:
-- - checkpoints: Main checkpoint data
-- - checkpoint_blobs: Large binary data 
-- - checkpoint_writes: Write operations log

-- Create indices for better performance (LangGraph creates these automatically)
-- This is just for reference - the actual tables are created by LangGraph

COMMENT ON DATABASE langgraph_checkpoints IS 'LangGraph Travel Agent state persistence database';
