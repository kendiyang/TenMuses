#!/usr/bin/env python
"""
Simple test to verify the enum fix works - just fetch workflows.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.workflow import Workflow, WorkflowStatus

async def test_enum_fix():
    """Test that workflows can be fetched without enum errors."""
    
    async with AsyncSessionLocal() as session:
        print("\n" + "="*60)
        print("  ENUM FIX VERIFICATION TEST")
        print("="*60 + "\n")
        
        try:
            print("📍 Fetching all workflows from database...")
            stmt = select(Workflow)
            result = await session.execute(stmt)
            workflows = result.scalars().all()
            
            print(f"\n✅ SUCCESS! Found {len(workflows)} workflow(s)\n")
            
            for i, wf in enumerate(workflows, 1):
                try:
                    status_enum = WorkflowStatus(wf.status)
                    status_name = status_enum.name
                except ValueError:
                    status_name = f"INVALID({wf.status})"
                
                print(f"  Workflow {i}:")
                print(f"    ID:     {wf.id}")
                print(f"    Title:  {wf.title}")
                print(f"    Status: {wf.status} -> {status_name}")
                print()
            
            print("="*60)
            print("✅ ENUM FIX VERIFIED - No LookupError!")
            print("="*60 + "\n")
            return True
            
        except LookupError as e:
            print(f"\n❌ ENUM FIX FAILED: {e}\n")
            return False
        except Exception as e:
            print(f"\n⚠️  Unexpected error: {e}\n")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_enum_fix())
    sys.exit(0 if success else 1)
