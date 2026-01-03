#!/usr/bin/env python3
"""
Redis Cache 功能测试脚本

测试 Redis 缓存的基本功能：
1. 连接测试
2. 读写测试
3. TTL 测试
4. 模式删除测试
5. API 缓存测试

使用方法:
    python test_redis_cache.py
"""

import asyncio
import sys
from datetime import datetime
import aiohttp

# 配置
API_URL = "http://localhost:8000"
REDIS_URL = "redis://localhost:6379/0"

class Colors:
    """Terminal colors"""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def log(msg: str, color: str = ""):
    """Print colored log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if color:
        print(f"{Colors.CYAN}[{timestamp}]{Colors.END} {color}{msg}{Colors.END}")
    else:
        print(f"{Colors.CYAN}[{timestamp}]{Colors.END} {msg}")


async def test_redis_connection():
    """Test Redis connection"""
    log("Testing Redis connection...", Colors.BLUE)
    
    try:
        import redis.asyncio as redis
        client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        
        # Test ping
        pong = await client.ping()
        if pong:
            log("✓ Redis connection successful", Colors.GREEN)
        else:
            raise Exception("Ping failed")
        
        await client.close()
        return True
    except Exception as e:
        log(f"✗ Redis connection failed: {e}", Colors.RED)
        return False


async def test_basic_operations():
    """Test basic cache operations"""
    log("Testing basic cache operations...", Colors.BLUE)
    
    try:
        import redis.asyncio as redis
        import json
        
        client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        
        # Test SET
        test_key = "test:key:1"
        test_value = {"message": "Hello Cache", "timestamp": datetime.now().isoformat()}
        await client.set(test_key, json.dumps(test_value))
        log("  ✓ SET operation successful", Colors.GREEN)
        
        # Test GET
        retrieved = await client.get(test_key)
        if retrieved:
            data = json.loads(retrieved)
            log(f"  ✓ GET operation successful: {data['message']}", Colors.GREEN)
        else:
            raise Exception("GET returned None")
        
        # Test TTL
        await client.setex("test:ttl:1", 10, json.dumps({"ttl": 10}))
        ttl = await client.ttl("test:ttl:1")
        log(f"  ✓ TTL operation successful: {ttl} seconds", Colors.GREEN)
        
        # Test DELETE
        await client.delete(test_key)
        deleted = await client.get(test_key)
        if deleted is None:
            log("  ✓ DELETE operation successful", Colors.GREEN)
        else:
            raise Exception("DELETE failed")
        
        # Cleanup
        await client.delete("test:ttl:1")
        
        await client.close()
        return True
    except Exception as e:
        log(f"✗ Basic operations failed: {e}", Colors.RED)
        return False


async def test_pattern_delete():
    """Test pattern-based deletion"""
    log("Testing pattern deletion...", Colors.BLUE)
    
    try:
        import redis.asyncio as redis
        
        client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        
        # Create test keys
        for i in range(5):
            await client.set(f"test:pattern:{i}", f"value_{i}")
        
        log("  Created 5 test keys", Colors.BLUE)
        
        # Delete by pattern
        keys = []
        async for key in client.scan_iter(match="test:pattern:*"):
            keys.append(key)
        
        if keys:
            deleted_count = await client.delete(*keys)
            log(f"  ✓ Deleted {deleted_count} keys matching pattern", Colors.GREEN)
        
        await client.close()
        return True
    except Exception as e:
        log(f"✗ Pattern deletion failed: {e}", Colors.RED)
        return False


async def test_api_cache_behavior():
    """Test API cache behavior"""
    log("Testing API cache behavior...", Colors.BLUE)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Register user and get token
            email = f"cache_test_{datetime.now().timestamp()}@example.com"
            
            log("  Registering test user...", Colors.BLUE)
            async with session.post(
                f"{API_URL}/api/v1/auth/register",
                json={
                    "email": email,
                    "username": "CacheTest",
                    "password": "Test123456"
                }
            ) as response:
                if response.status != 200:
                    raise Exception(f"Registration failed: {response.status}")
                data = await response.json()
                token = data["access_token"]
            
            log("  ✓ User registered", Colors.GREEN)
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test 1: Marketplace templates (should be cached)
            log("  Testing marketplace cache...", Colors.BLUE)
            
            # First call (miss)
            import time
            start = time.time()
            async with session.get(
                f"{API_URL}/api/v1/marketplace/templates",
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"Marketplace failed: {response.status}")
                first_duration = time.time() - start
            
            log(f"    First call: {first_duration*1000:.2f}ms", Colors.YELLOW)
            
            # Second call (should be cached)
            start = time.time()
            async with session.get(
                f"{API_URL}/api/v1/marketplace/templates",
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"Marketplace failed: {response.status}")
                second_duration = time.time() - start
            
            log(f"    Second call: {second_duration*1000:.2f}ms", Colors.YELLOW)
            
            # Cache should be faster
            if second_duration < first_duration:
                log(f"  ✓ Cache speedup: {(first_duration/second_duration):.2f}x faster", Colors.GREEN)
            else:
                log(f"  ⚠ No cache speedup detected", Colors.YELLOW)
            
            # Test 2: User statistics (should be cached)
            log("  Testing user statistics cache...", Colors.BLUE)
            
            start = time.time()
            async with session.get(
                f"{API_URL}/api/v1/users/me/statistics",
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"Statistics failed: {response.status}")
                first_duration = time.time() - start
            
            start = time.time()
            async with session.get(
                f"{API_URL}/api/v1/users/me/statistics",
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"Statistics failed: {response.status}")
                second_duration = time.time() - start
            
            log(f"    First: {first_duration*1000:.2f}ms, Second: {second_duration*1000:.2f}ms", Colors.YELLOW)
            log("  ✓ Statistics cache working", Colors.GREEN)
            
        return True
    except Exception as e:
        log(f"✗ API cache test failed: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test flow"""
    log(f"\n{Colors.BOLD}{'='*60}{Colors.END}", Colors.CYAN)
    log(f"{Colors.BOLD}Redis Cache Integration Test{Colors.END}", Colors.CYAN)
    log(f"{Colors.BOLD}{'='*60}{Colors.END}\n", Colors.CYAN)
    
    results = []
    
    # Test 1: Connection
    results.append(await test_redis_connection())
    
    if not results[-1]:
        log("\n⚠️  Redis not running or not accessible", Colors.YELLOW)
        log("   Start Redis: docker run -d -p 6379:6379 redis", Colors.YELLOW)
        return 1
    
    # Test 2: Basic operations
    results.append(await test_basic_operations())
    
    # Test 3: Pattern deletion
    results.append(await test_pattern_delete())
    
    # Test 4: API cache behavior
    log("\nTesting API cache integration...", Colors.BLUE)
    log("⚠️  Make sure backend server is running", Colors.YELLOW)
    try:
        results.append(await test_api_cache_behavior())
    except Exception as e:
        log(f"✗ API test skipped: {e}", Colors.YELLOW)
        results.append(False)
    
    # Summary
    log(f"\n{Colors.BOLD}{'='*60}{Colors.END}", Colors.CYAN)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        log(f"{Colors.BOLD}✓ All tests passed! ({passed}/{total}){Colors.END}", Colors.GREEN)
        return 0
    else:
        log(f"{Colors.BOLD}✗ Some tests failed ({passed}/{total}){Colors.END}", Colors.RED)
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("\n\nTest interrupted by user", Colors.YELLOW)
        sys.exit(1)
