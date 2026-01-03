#!/usr/bin/env python
"""Initialize marketplace with sample templates"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.template import Template
from uuid import uuid4
from datetime import datetime

async def init_templates():
    """Initialize sample templates in the database"""
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    # Create async session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Sample templates
        templates_data = [
            {
                "name": "Content Research & Summarization",
                "description": "Automated research collection and intelligent summarization for content creators",
                "category": "Content Creation",
                "tags": ["research", "summarization", "content"],
                "rating": 4.8,
                "use_count": 234,
                "favorite_count": 45,
                "is_featured": True,
            },
            {
                "name": "Email Marketing Campaign Generator",
                "description": "Generate personalized email campaigns with AI-powered copywriting",
                "category": "Marketing",
                "tags": ["email", "marketing", "copywriting"],
                "rating": 4.6,
                "use_count": 189,
                "favorite_count": 32,
                "is_featured": True,
            },
            {
                "name": "Data Analysis & Insights",
                "description": "Analyze datasets and generate actionable business insights",
                "category": "Data Analysis",
                "tags": ["data", "analysis", "insights"],
                "rating": 4.9,
                "use_count": 312,
                "favorite_count": 67,
                "is_featured": True,
            },
            {
                "name": "Social Media Content Planner",
                "description": "Plan and schedule social media content with AI suggestions",
                "category": "Marketing",
                "tags": ["social", "content", "marketing"],
                "rating": 4.5,
                "use_count": 156,
                "favorite_count": 28,
                "is_featured": False,
            },
            {
                "name": "Customer Feedback Analysis",
                "description": "Collect and analyze customer feedback to identify improvement areas",
                "category": "Business",
                "tags": ["feedback", "analysis", "customer"],
                "rating": 4.7,
                "use_count": 203,
                "favorite_count": 41,
                "is_featured": True,
            },
            {
                "name": "Blog Post Generator",
                "description": "Generate complete blog posts from topics with SEO optimization",
                "category": "Content Creation",
                "tags": ["blog", "content", "seo"],
                "rating": 4.4,
                "use_count": 178,
                "favorite_count": 33,
                "is_featured": False,
            },
            {
                "name": "Lead Generation & Qualification",
                "description": "Identify and qualify leads automatically from various sources",
                "category": "Business",
                "tags": ["leads", "sales", "automation"],
                "rating": 4.8,
                "use_count": 267,
                "favorite_count": 52,
                "is_featured": True,
            },
            {
                "name": "Product Description Writer",
                "description": "Create compelling product descriptions that drive conversions",
                "category": "Content Creation",
                "tags": ["product", "descriptions", "ecommerce"],
                "rating": 4.6,
                "use_count": 145,
                "favorite_count": 24,
                "is_featured": False,
            },
            {
                "name": "Code Documentation Generator",
                "description": "Automatically generate documentation from source code",
                "category": "Development",
                "tags": ["code", "documentation", "development"],
                "rating": 4.9,
                "use_count": 198,
                "favorite_count": 39,
                "is_featured": True,
            },
            {
                "name": "Competitive Analysis Report",
                "description": "Generate detailed competitive analysis reports from market data",
                "category": "Business",
                "tags": ["competitive", "analysis", "market"],
                "rating": 4.5,
                "use_count": 134,
                "favorite_count": 22,
                "is_featured": False,
            },
        ]
        
        # Check if templates already exist
        from sqlalchemy import select
        result = await session.execute(select(Template))
        existing = result.scalars().all()
        
        if existing:
            print(f"✅ Found {len(existing)} existing templates. Skipping initialization.")
            return
        
        # Create templates
        for data in templates_data:
            template = Template(
                id=uuid4(),
                name=data["name"],
                description=data["description"],
                category=data["category"],
                tags=data["tags"],
                rating=data["rating"],
                use_count=data["use_count"],
                favorite_count=data["favorite_count"],
                is_featured=data["is_featured"],
                author_id="system",  # System-created templates
                workflow_config={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(template)
        
        await session.commit()
        print(f"✅ Successfully initialized {len(templates_data)} sample templates!")

if __name__ == "__main__":
    asyncio.run(init_templates())
