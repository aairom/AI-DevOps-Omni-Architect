"""
Async cache management for AI responses
Supports both in-memory and Redis caching with async operations
"""
import json
import hashlib
import logging
import asyncio
from typing import Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AsyncCacheManager:
    """Manages async caching of AI responses"""
    
    def __init__(self, use_redis: bool = False, redis_config: Optional[dict] = None):
        self.use_redis = use_redis
        self.memory_cache = {}
        self.redis_client = None
        self._lock = asyncio.Lock()
        
        if use_redis:
            try:
                import redis.asyncio as aioredis
                config = redis_config or {}
                self.redis_client = aioredis.Redis(
                    host=config.get('host', 'localhost'),
                    port=config.get('port', 6379),
                    db=config.get('db', 0),
                    decode_responses=True
                )
                logger.info("Async Redis cache initialized")
            except Exception as e:
                logger.warning(f"Async Redis initialization failed, using memory cache: {e}")
                self.use_redis = False
    
    async def ping_redis(self) -> bool:
        """Test Redis connection"""
        if self.redis_client:
            try:
                await self.redis_client.ping()
                return True
            except:
                return False
        return False
    
    def _generate_key(self, prompt: str, provider: str, model: str) -> str:
        """Generate cache key from prompt and model info"""
        content = f"{provider}:{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def get(self, prompt: str, provider: str, model: str) -> Optional[str]:
        """Retrieve cached response asynchronously"""
        key = self._generate_key(prompt, provider, model)
        
        try:
            if self.use_redis and self.redis_client:
                cached = await self.redis_client.get(key)
                if cached:
                    logger.info(f"Cache hit (Redis): {key[:16]}...")
                    return cached
            else:
                async with self._lock:
                    if key in self.memory_cache:
                        entry = self.memory_cache[key]
                        # Check if expired
                        if datetime.now() < entry['expires']:
                            logger.info(f"Cache hit (Memory): {key[:16]}...")
                            return entry['value']
                        else:
                            del self.memory_cache[key]
        except Exception as e:
            logger.error(f"Async cache retrieval error: {e}")
        
        return None
    
    async def set(self, prompt: str, provider: str, model: str, response: str, ttl: int = 3600):
        """Store response in cache asynchronously"""
        key = self._generate_key(prompt, provider, model)
        
        try:
            if self.use_redis and self.redis_client:
                await self.redis_client.setex(key, ttl, response)
                logger.info(f"Cached to Redis: {key[:16]}...")
            else:
                async with self._lock:
                    self.memory_cache[key] = {
                        'value': response,
                        'expires': datetime.now() + timedelta(seconds=ttl)
                    }
                    logger.info(f"Cached to Memory: {key[:16]}...")
                    
                    # Limit memory cache size
                    if len(self.memory_cache) > 100:
                        await self._cleanup_memory_cache()
        except Exception as e:
            logger.error(f"Async cache storage error: {e}")
    
    async def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache"""
        now = datetime.now()
        async with self._lock:
            expired_keys = [k for k, v in self.memory_cache.items() if now >= v['expires']]
            for key in expired_keys:
                del self.memory_cache[key]
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def clear(self):
        """Clear all cache asynchronously"""
        try:
            if self.use_redis and self.redis_client:
                await self.redis_client.flushdb()
                logger.info("Redis cache cleared")
            async with self._lock:
                self.memory_cache.clear()
                logger.info("Memory cache cleared")
        except Exception as e:
            logger.error(f"Async cache clear error: {e}")
    
    async def get_stats(self) -> dict:
        """Get cache statistics asynchronously"""
        stats = {
            'type': 'redis' if self.use_redis else 'memory',
            'memory_entries': len(self.memory_cache)
        }
        
        if self.use_redis and self.redis_client:
            try:
                info = await self.redis_client.info('stats')
                stats['redis_keys'] = await self.redis_client.dbsize()
                stats['redis_hits'] = info.get('keyspace_hits', 0)
                stats['redis_misses'] = info.get('keyspace_misses', 0)
            except Exception as e:
                logger.error(f"Error getting async Redis stats: {e}")
        
        return stats
    
    async def batch_get(self, requests: list[tuple[str, str, str]]) -> list[Optional[str]]:
        """Get multiple cached responses concurrently"""
        tasks = [self.get(prompt, provider, model) for prompt, provider, model in requests]
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    async def batch_set(self, items: list[tuple[str, str, str, str, int]]):
        """Set multiple cache entries concurrently"""
        tasks = [
            self.set(prompt, provider, model, response, ttl)
            for prompt, provider, model, response, ttl in items
        ]
        await asyncio.gather(*tasks, return_exceptions=False)
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

# Global async cache manager instance
async_cache_manager = AsyncCacheManager()

# Made with Bob