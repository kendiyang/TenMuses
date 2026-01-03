"""
Cache invalidation helpers for TenMuses platform.

Provides functions to invalidate cache when data changes.
"""

from app.core.cache import cache_service


async def invalidate_marketplace_cache():
    """Invalidate all marketplace template caches"""
    await cache_service.delete_pattern("marketplace:*")


async def invalidate_template_cache(template_id: str):
    """Invalidate specific template cache"""
    await cache_service.delete(f"template:{template_id}")
    # Also invalidate marketplace lists
    await invalidate_marketplace_cache()


async def invalidate_user_statistics_cache(user_id: str):
    """Invalidate user statistics cache"""
    await cache_service.delete(f"user:{user_id}:stats")


async def invalidate_llm_cache():
    """Invalidate LLM provider/model caches"""
    await cache_service.delete_pattern("llm:*")


async def invalidate_all_caches():
    """Invalidate all caches (use with caution)"""
    await cache_service.delete_pattern("*")
