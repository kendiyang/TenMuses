"""
Redis cache service for TenMuses platform.

Provides caching for:
- Marketplace template lists
- User statistics
- LLM provider configurations
- Template details
"""

import json
import redis.asyncio as redis
from typing import Optional, Any
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Async Redis cache service"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize Redis cache service.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            self._connected = True
            logger.info(f"✓ Redis connected: {self.redis_url}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
            self._connected = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Redis disconnected")
    
    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self._connected
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.is_connected or not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = 300  # Default 5 minutes
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                await self.redis_client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.is_connected or not self.redis_client:
            return 0
        
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter.
        
        Args:
            key: Cache key
            amount: Amount to increment
            
        Returns:
            New value or None
        """
        if not self.is_connected or not self.redis_client:
            return None
        
        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get TTL for key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds or None
        """
        if not self.is_connected or not self.redis_client:
            return None
        
        try:
            ttl = await self.redis_client.ttl(key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return None


# Global cache service instance
cache_service = CacheService()


# Cache key generators
class CacheKeys:
    """Cache key generators for different data types"""
    
    @staticmethod
    def marketplace_templates(
        category: Optional[str] = None,
        tags: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "popular",
        page: int = 1,
        page_size: int = 20
    ) -> str:
        """Generate cache key for marketplace template list"""
        parts = ["marketplace", "templates", sort_by, str(page), str(page_size)]
        if category:
            parts.append(f"cat:{category}")
        if tags:
            parts.append(f"tags:{tags}")
        if search:
            parts.append(f"search:{search}")
        return ":".join(parts)
    
    @staticmethod
    def template_detail(template_id: str) -> str:
        """Generate cache key for template detail"""
        return f"template:{template_id}"
    
    @staticmethod
    def user_statistics(user_id: str) -> str:
        """Generate cache key for user statistics"""
        return f"user:{user_id}:stats"
    
    @staticmethod
    def featured_templates() -> str:
        """Generate cache key for featured templates"""
        return "marketplace:templates:featured"
    
    @staticmethod
    def llm_providers() -> str:
        """Generate cache key for LLM providers"""
        return "llm:providers"
    
    @staticmethod
    def llm_models(provider: str) -> str:
        """Generate cache key for LLM models"""
        return f"llm:models:{provider}"


# Cache TTL constants (in seconds)
class CacheTTL:
    """Cache TTL values for different data types"""
    
    MARKETPLACE_TEMPLATES = 300  # 5 minutes
    TEMPLATE_DETAIL = 600  # 10 minutes
    USER_STATISTICS = 180  # 3 minutes
    FEATURED_TEMPLATES = 600  # 10 minutes
    LLM_PROVIDERS = 3600  # 1 hour
    LLM_MODELS = 3600  # 1 hour
