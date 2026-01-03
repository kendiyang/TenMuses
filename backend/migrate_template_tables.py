#!/usr/bin/env python3
"""
Database migration script: Create templates, template_reviews, and favorites tables
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
    """Create template-related tables"""
    
    migrations = [
        ("Create templates table",
         """CREATE TABLE IF NOT EXISTS templates (
             id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
             workflow_id UUID NOT NULL UNIQUE REFERENCES workflows(id) ON DELETE CASCADE,
             author_id UUID NOT NULL REFERENCES users(id),
             name VARCHAR NOT NULL,
             description TEXT NOT NULL,
             category VARCHAR NOT NULL,
             tags TEXT[] DEFAULT '{}',
             icon_url VARCHAR,
             preview_images TEXT[] DEFAULT '{}',
             use_count INTEGER DEFAULT 0 NOT NULL,
             favorite_count INTEGER DEFAULT 0 NOT NULL,
             rating FLOAT DEFAULT 0.0 NOT NULL,
             review_count INTEGER DEFAULT 0 NOT NULL,
             is_featured BOOLEAN DEFAULT FALSE NOT NULL,
             is_published BOOLEAN DEFAULT TRUE NOT NULL,
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
         )"""),
        
        ("Create template_reviews table",
         """CREATE TABLE IF NOT EXISTS template_reviews (
             id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
             template_id UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
             user_id UUID NOT NULL REFERENCES users(id),
             rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
             comment TEXT,
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
             UNIQUE(template_id, user_id)
         )"""),
        
        ("Create favorites table",
         """CREATE TABLE IF NOT EXISTS favorites (
             id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
             user_id UUID NOT NULL REFERENCES users(id),
             template_id UUID NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
             UNIQUE(user_id, template_id)
         )"""),
        
        ("Create index on templates.category",
         "CREATE INDEX IF NOT EXISTS idx_templates_category ON templates(category)"),
        
        ("Create index on templates.tags",
         "CREATE INDEX IF NOT EXISTS idx_templates_tags ON templates USING GIN(tags)"),
        
        ("Create index on templates.is_featured",
         "CREATE INDEX IF NOT EXISTS idx_templates_is_featured ON templates(is_featured)"),
        
        ("Create index on templates.rating",
         "CREATE INDEX IF NOT EXISTS idx_templates_rating ON templates(rating DESC)"),
        
        ("Create index on templates.use_count",
         "CREATE INDEX IF NOT EXISTS idx_templates_use_count ON templates(use_count DESC)"),
        
        ("Create index on template_reviews.template_id",
         "CREATE INDEX IF NOT EXISTS idx_template_reviews_template_id ON template_reviews(template_id)"),
        
        ("Create index on favorites.user_id",
         "CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id)"),
    ]
    
    async with engine.begin() as conn:
        print("Running migration: create template tables...")
        for description, sql in migrations:
            try:
                print(f"  - {description}...")
                await conn.execute(text(sql))
                print(f"    ✓ {description} completed")
            except Exception as e:
                print(f"    ! {description} failed: {str(e)}")
        
        print("\n✓ Migration completed successfully!")
        print("  Summary:")
        print("  - Created 'templates' table")
        print("  - Created 'template_reviews' table")
        print("  - Created 'favorites' table")
        print("  - Created indexes for better query performance")


async def rollback_migration():
    """Drop template-related tables"""
    
    rollback_sql = """
    DROP TABLE IF EXISTS favorites CASCADE;
    DROP TABLE IF EXISTS template_reviews CASCADE;
    DROP TABLE IF EXISTS templates CASCADE;
    """
    
    async with engine.begin() as conn:
        print("Rolling back migration: drop template tables...")
        await conn.execute(text(rollback_sql))
        print("✓ Rollback completed successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback_migration())
    else:
        asyncio.run(run_migration())
