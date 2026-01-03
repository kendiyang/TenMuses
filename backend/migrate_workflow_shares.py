#!/usr/bin/env python3
"""
Database migration script: Create workflow_shares and workflow_share_access tables
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
    """Create workflow share tables"""
    
    migrations = [
        ("Create workflow_shares table",
         """CREATE TABLE IF NOT EXISTS workflow_shares (
             id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
             workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
             owner_id UUID NOT NULL REFERENCES users(id),
             share_token VARCHAR NOT NULL UNIQUE,
             share_url VARCHAR,
             permission VARCHAR NOT NULL DEFAULT 'view',
             is_public BOOLEAN DEFAULT FALSE NOT NULL,
             max_uses VARCHAR,
             current_uses VARCHAR DEFAULT '0' NOT NULL,
             expires_at TIMESTAMP,
             description TEXT,
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
         )"""),
        
        ("Create workflow_share_access table",
         """CREATE TABLE IF NOT EXISTS workflow_share_access (
             id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
             share_id UUID NOT NULL REFERENCES workflow_shares(id) ON DELETE CASCADE,
             access_token VARCHAR UNIQUE,
             accessed_by UUID REFERENCES users(id),
             accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
             ip_address VARCHAR,
             user_agent VARCHAR
         )"""),
        
        ("Create index on workflow_shares.share_token",
         "CREATE INDEX IF NOT EXISTS idx_workflow_shares_token ON workflow_shares(share_token)"),
        
        ("Create index on workflow_shares.workflow_id",
         "CREATE INDEX IF NOT EXISTS idx_workflow_shares_workflow ON workflow_shares(workflow_id)"),
        
        ("Create index on workflow_shares.owner_id",
         "CREATE INDEX IF NOT EXISTS idx_workflow_shares_owner ON workflow_shares(owner_id)"),
        
        ("Create index on workflow_share_access.share_id",
         "CREATE INDEX IF NOT EXISTS idx_share_access_share ON workflow_share_access(share_id)"),
    ]
    
    async with engine.begin() as conn:
        print("Running migration: create workflow share tables...")
        for description, sql in migrations:
            try:
                print(f"  - {description}...")
                await conn.execute(text(sql))
                print(f"    ✓ {description} completed")
            except Exception as e:
                print(f"    ! {description} failed: {str(e)}")
        
        print("\n✓ Migration completed successfully!")
        print("  Summary:")
        print("  - Created 'workflow_shares' table")
        print("  - Created 'workflow_share_access' table")
        print("  - Created indexes for better query performance")


async def rollback_migration():
    """Drop workflow share tables"""
    
    rollback_sql = """
    DROP TABLE IF EXISTS workflow_share_access CASCADE;
    DROP TABLE IF EXISTS workflow_shares CASCADE;
    """
    
    async with engine.begin() as conn:
        print("Rolling back migration: drop workflow share tables...")
        await conn.execute(text(rollback_sql))
        print("✓ Rollback completed successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback_migration())
    else:
        asyncio.run(run_migration())
