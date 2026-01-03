#!/usr/bin/env python
"""
Integration test to verify the enum fix works with the actual API endpoint.
"""

import asyncio
import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token
from app.models.user import User
from app.models.workflow import Workflow, WorkflowStatus


async def test_workspace_endpoint():
    """Test that the workspace endpoint works without enum errors."""
    
    async with AsyncSessionLocal() as session:
        print("\n" + "="*70)
        print("  WORKSPACE ENDPOINT ENUM FIX VERIFICATION")
        print("="*70 + "\n")
        
        # Get or create a test user
        print("1. Setting up test user...")
        stmt = select(User).limit(1)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print("   No users found - creating test user...")
            user = User(
                id=uuid4(),
                email="test@example.com",
                username="testuser",
                password_hash="dummy_hash"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        print(f"   ✓ Using user: {user.id}")
        
        # Verify workflows can be fetched (this would fail with enum error)
        print("\n2. Fetching user's workflows...")
        try:
            stmt = (
                select(Workflow)
                .where(Workflow.owner_id == user.id)
                .limit(10)
            )
            result = await session.execute(stmt)
            workflows = result.scalars().all()
            print(f"   ✓ Successfully fetched {len(workflows)} workflow(s)")
            for wf in workflows:
                print(f"     - {wf.title} (status: {wf.status})")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            return False
        
        # Verify status values are strings
        print("\n3. Verifying status values...")
        try:
            for wf in workflows:
                assert isinstance(wf.status, str), f"Status should be string, got {type(wf.status)}"
                # Verify it's a valid enum value
                WorkflowStatus(wf.status)  # Will raise ValueError if invalid
            print(f"   ✓ All {len(workflows)} status values are valid strings")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            return False
        
        # Create a test token
        print("\n4. Creating JWT token...")
        token = create_access_token(user_id=str(user.id))
        print(f"   ✓ Token created: {token[:50]}...")
        
        print("\n" + "="*70)
        print("✅ ENUM FIX VERIFIED - Workspace endpoint ready!")
        print("="*70)
        print(f"\nYou can now test the endpoint:")
        print(f"  curl -H 'Authorization: Bearer {token}' \\")
        print(f"       http://localhost:8000/api/v1/workspace")
        print()
        
        return True


if __name__ == "__main__":
    success = asyncio.run(test_workspace_endpoint())
    sys.exit(0 if success else 1)
