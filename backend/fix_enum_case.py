#!/usr/bin/env python
"""
Fix the WorkflowStatus enum case mismatch.

The issue: PostgreSQL's native enum type 'workflowstatus' is defined with lowercase
values ('draft', 'published', 'running'), but SQLAlchemy needs to work with string
values directly when native_enum=False.

The fix: Drop the native enum type and use plain VARCHAR instead, since SQLAlchemy
with native_enum=False will handle the enum validation at the Python level.
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.core.database import engine

async def fix_enum():
    async with engine.begin() as conn:
        print("Fixing WorkflowStatus enum mismatch...\n")
        
        # Check if workflowstatus type exists
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'workflows'
            );
        """))
        workflows_exist = result.scalar()
        
        if not workflows_exist:
            print("✓ workflows table doesn't exist yet, no fix needed")
            return
        
        # Check the current column type
        result = await conn.execute(text("""
            SELECT data_type FROM information_schema.columns 
            WHERE table_name = 'workflows' AND column_name = 'status';
        """))
        current_type = result.scalar()
        print(f"Current status column type: {current_type}")
        
        if current_type == 'USER-DEFINED':
            print("\nStep 1: Casting status column to VARCHAR...")
            await conn.execute(text("""
                ALTER TABLE workflows 
                ALTER COLUMN status TYPE VARCHAR;
            """))
            print("✓ Column converted to VARCHAR")
            
            print("Step 2: Dropping workflowstatus enum type...")
            await conn.execute(text("""
                DROP TYPE IF EXISTS workflowstatus CASCADE;
            """))
            print("✓ Enum type dropped")
        
        print("\n✅ Database schema fixed! Status column is now VARCHAR.")
        print("   SQLAlchemy will handle enum validation at the Python level.")

if __name__ == "__main__":
    asyncio.run(fix_enum())
