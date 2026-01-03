#!/usr/bin/env python
"""
Test script to verify the enum fix works correctly.
"""

import asyncio
import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, AsyncSessionLocal
from app.models.workflow import Workflow, WorkflowStatus

async def test_enum_fix():
    """Test that workflows can be fetched and created without enum errors."""
    
    async with AsyncSessionLocal() as session:
        print("Testing Workflow Status Enum Fix\n" + "="*50)
        
        # Test 1: Fetch all workflows (this was failing before)
        print("\n✓ Test 1: Fetching workflows from database...")
        try:
            stmt = select(Workflow)
            result = await session.execute(stmt)
            workflows = result.scalars().all()
            print(f"  Found {len(workflows)} workflows")
            for wf in workflows:
                print(f"    - {wf.id}: status={wf.status} (type: {type(wf.status).__name__})")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
        
        # Test 2: Create a new workflow with enum
        print("\n✓ Test 2: Creating new workflow with status enum...")
        try:
            new_workflow = Workflow(
                id=uuid4(),
                owner_id=uuid4(),
                title="Test Workflow",
                description="Testing enum",
                canvas_json={},
                status=WorkflowStatus.DRAFT
            )
            session.add(new_workflow)
            await session.commit()
            print(f"  Created workflow: {new_workflow.id}")
            print(f"  Status: {new_workflow.status} (type: {type(new_workflow.status).__name__})")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            await session.rollback()
            return False
        
        # Test 3: Query and verify the created workflow
        print("\n✓ Test 3: Fetching the created workflow...")
        try:
            stmt = select(Workflow).where(Workflow.id == new_workflow.id)
            result = await session.execute(stmt)
            fetched = result.scalar_one_or_none()
            if fetched:
                print(f"  Fetched workflow: {fetched.id}")
                print(f"  Status: {fetched.status} (type: {type(fetched.status).__name__})")
                print(f"  Status is DRAFT enum: {fetched.status == WorkflowStatus.DRAFT}")
            else:
                print(f"  ❌ Workflow not found!")
                return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
        
        # Test 4: Test all enum values
        print("\n✓ Test 4: Testing all enum values...")
        try:
            for status_value in WorkflowStatus:
                wf = Workflow(
                    id=uuid4(),
                    owner_id=uuid4(),
                    title=f"Test {status_value.name}",
                    canvas_json={},
                    status=status_value
                )
                session.add(wf)
            await session.commit()
            print(f"  Created workflows for all statuses: {[s.value for s in WorkflowStatus]}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            await session.rollback()
            return False
        
        print("\n" + "="*50)
        print("✅ All tests passed! Enum fix is working correctly.")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_enum_fix())
    sys.exit(0 if success else 1)
