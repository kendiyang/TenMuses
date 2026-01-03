-- Add new fields to workflows table
-- Run this migration to add tags, status, and last_run_at fields

-- Add tags field (array of strings)
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- Add WorkflowStatus enum type
DO $$ BEGIN
    CREATE TYPE workflowstatus AS ENUM ('draft', 'published', 'running');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add status field with default value 'draft'
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS status workflowstatus DEFAULT 'draft' NOT NULL;

-- Add last_run_at timestamp field
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS last_run_at TIMESTAMP;

-- Create index on tags for faster filtering
CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflows USING GIN(tags);

-- Create index on status for faster filtering
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);

-- Create index on last_run_at for sorting recent workflows
CREATE INDEX IF NOT EXISTS idx_workflows_last_run_at ON workflows(last_run_at DESC);
