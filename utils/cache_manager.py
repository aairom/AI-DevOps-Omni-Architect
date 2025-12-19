"""
Cache management for AI responses
Supports both in-memory and Redis caching
"""
import json
import hashlib
import logging
from typing import Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages caching of AI responses"""
    
    def __init__(self, use_redis: bool = False, redis_config: Optional[dict] = None):
        self.use_redis = use_redis
        self.memory_cache = {}
        self.redis_client = None
        
        if use_redis:
            try:
                import redis
                config = redis_config or {}
                self.redis_client = redis.Redis(
                    host=config.get('host', 'localhost'),
                    port=config.get('port', 6379),
                    db=config.get('db', 0),
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis initialization failed, falling back to memory cache: {e}")
                self.use_redis = False
    
    def _generate_key(self, prompt: str, provider: str, model: str) -> str:
        """Generate cache key from prompt and model info"""
        content = f"{provider}:{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, prompt: str, provider: str, model: str) -> Optional[str]:
        """Retrieve cached response"""
        key = self._generate_key(prompt, provider, model)
        
        try:
            if self.use_redis and self.redis_client:
                cached = self.redis_client.get(key)
                if cached:
                    logger.info(f"Cache hit (Redis): {key[:16]}...")
                    return cached
            else:
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    # Check if expired
                    if datetime.now() < entry['expires']:
                        logger.info(f"Cache hit (Memory): {key[:16]}...")
                        return entry['value']
                    else:
                        del self.memory_cache[key]
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        
        return None
    
    def set(self, prompt: str, provider: str, model: str, response: str, ttl: int = 3600):
        """Store response in cache"""
        key = self._generate_key(prompt, provider, model)
        
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.setex(key, ttl, response)
                logger.info(f"Cached to Redis: {key[:16]}...")
            else:
                self.memory_cache[key] = {
                    'value': response,
                    'expires': datetime.now() + timedelta(seconds=ttl)
                }
                logger.info(f"Cached to Memory: {key[:16]}...")
                
                # Limit memory cache size
                if len(self.memory_cache) > 100:
                    self._cleanup_memory_cache()
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
    
    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache"""
        now = datetime.now()
        expired_keys = [k for k, v in self.memory_cache.items() if now >= v['expires']]
        for key in expired_keys:
            del self.memory_cache[key]
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def clear(self):
        """Clear all cache"""
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.flushdb()
                logger.info("Redis cache cleared")
            self.memory_cache.clear()
            logger.info("Memory cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        stats = {
            'type': 'redis' if self.use_redis else 'memory',
            'memory_entries': len(self.memory_cache)
        }
        
        if self.use_redis and self.redis_client:
            try:
                info = self.redis_client.info('stats')
                stats['redis_keys'] = self.redis_client.dbsize()
                stats['redis_hits'] = info.get('keyspace_hits', 0)
                stats['redis_misses'] = info.get('keyspace_misses', 0)
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")
        
        return stats

# Global cache manager instance
cache_manager = CacheManager()

# Made with Bob
