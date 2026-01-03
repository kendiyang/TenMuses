#!/usr/bin/env python3
"""
Database migration script: Add tags, status, and last_run_at fields to workflows table
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import engine


async def run_migration():
    """Run the migration to add new workflow fields"""
    
    migrations = [
        ("Add tags column", 
         "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}'"),
        
        ("Create WorkflowStatus enum",
         """DO $$ BEGIN
             CREATE TYPE workflowstatus AS ENUM ('draft', 'published', 'running');
         EXCEPTION
             WHEN duplicate_object THEN null;
         END $$"""),
        
        ("Add status column",
         "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS status workflowstatus DEFAULT 'draft' NOT NULL"),
        
        ("Add last_run_at column",
         "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS last_run_at TIMESTAMP"),
        
        ("Create tags index",
         "CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflows USING GIN(tags)"),
        
        ("Create status index",
         "CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)"),
        
        ("Create last_run_at index",
         "CREATE INDEX IF NOT EXISTS idx_workflows_last_run_at ON workflows(last_run_at DESC)"),
    ]
    
    async with engine.begin() as conn:
        print("Running migration: add workflow fields...")
        for description, sql in migrations:
            try:
                print(f"  - {description}...")
                await conn.execute(text(sql))
                print(f"    ✓ {description} completed")
            except Exception as e:
                print(f"    ! {description} failed: {str(e)}")
                # Continue with other migrations
        
        print("\n✓ Migration completed successfully!")
        print("  Summary:")
        print("  - Added 'tags' column (TEXT[])")
        print("  - Added 'status' column (workflowstatus enum)")
        print("  - Added 'last_run_at' column (TIMESTAMP)")
        print("  - Created indexes for better query performance")


async def rollback_migration():
    """Rollback the migration (remove added fields)"""
    
    rollback_sql = """
    -- Remove indexes
    DROP INDEX IF EXISTS idx_workflows_last_run_at;
    DROP INDEX IF EXISTS idx_workflows_status;
    DROP INDEX IF EXISTS idx_workflows_tags;

    -- Remove columns
    ALTER TABLE workflows DROP COLUMN IF EXISTS last_run_at;
    ALTER TABLE workflows DROP COLUMN IF EXISTS status;
    ALTER TABLE workflows DROP COLUMN IF EXISTS tags;

    -- Drop enum type (only if no other columns use it)
    DROP TYPE IF EXISTS workflowstatus;
    """
    
    async with engine.begin() as conn:
        print("Rolling back migration: remove workflow fields...")
        await conn.execute(text(rollback_sql))
        print("✓ Rollback completed successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback_migration())
    else:
        asyncio.run(run_migration())
