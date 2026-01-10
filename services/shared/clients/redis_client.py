# =============================================================================
# Redis Client
# =============================================================================
# Client for Redis pub/sub messaging and caching
# =============================================================================

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Union
from functools import lru_cache

import redis.asyncio as redis
import structlog
from pydantic import BaseModel

from shared.config.settings import settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """
    Async Redis client for pub/sub messaging and caching.
    
    Provides:
    - Pub/Sub messaging for agent communication
    - Key-value caching with TTL
    - Distributed locking
    - Task queues
    """
    
    def __init__(self, url: Optional[str] = None):
        self.url = url or settings.redis.url
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self.logger = structlog.get_logger(__name__)
    
    async def connect(self) -> None:
        """Initialize the Redis connection pool."""
        if self._pool is None:
            self._pool = redis.ConnectionPool.from_url(
                self.url,
                max_connections=settings.redis.max_connections,
                decode_responses=settings.redis.decode_responses
            )
            self._client = redis.Redis(connection_pool=self._pool)
            self.logger.info("Redis connection pool initialized")
    
    async def disconnect(self) -> None:
        """Close the Redis connection pool."""
        if self._pubsub:
            await self._pubsub.close()
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        self.logger.info("Redis connection pool closed")
    
    @property
    async def client(self) -> redis.Redis:
        """Get the Redis client, connecting if necessary."""
        if self._client is None:
            await self.connect()
        return self._client
    
    # =========================================================================
    # Pub/Sub Methods
    # =========================================================================
    
    async def publish(self, channel: str, message: Union[str, Dict, BaseModel]) -> int:
        """
        Publish a message to a channel.
        
        Args:
            channel: Channel name
            message: Message to publish (string, dict, or Pydantic model)
            
        Returns:
            Number of subscribers that received the message
        """
        client = await self.client
        
        if isinstance(message, BaseModel):
            message = message.model_dump_json()
        elif isinstance(message, dict):
            message = json.dumps(message)
        
        result = await client.publish(channel, message)
        
        self.logger.debug(
            "Published message",
            channel=channel,
            subscribers=result
        )
        
        return result
    
    async def subscribe(
        self,
        channels: List[str],
        callback: Callable[[str, str], None]
    ) -> None:
        """
        Subscribe to channels and process messages.
        
        Args:
            channels: List of channel names to subscribe to
            callback: Async function to call with (channel, message)
        """
        client = await self.client
        self._pubsub = client.pubsub()
        
        await self._pubsub.subscribe(*channels)
        
        self.logger.info(
            "Subscribed to channels",
            channels=channels
        )
        
        async for message in self._pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"]
                data = message["data"]
                
                try:
                    await callback(channel, data)
                except Exception as e:
                    self.logger.error(
                        "Error processing message",
                        channel=channel,
                        error=str(e)
                    )
    
    async def unsubscribe(self, channels: Optional[List[str]] = None) -> None:
        """Unsubscribe from channels."""
        if self._pubsub:
            if channels:
                await self._pubsub.unsubscribe(*channels)
            else:
                await self._pubsub.unsubscribe()
    
    # =========================================================================
    # Caching Methods
    # =========================================================================
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value from cache."""
        client = await self.client
        return await client.get(key)
    
    async def get_json(self, key: str) -> Optional[Dict]:
        """Get a JSON value from cache."""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(
        self,
        key: str,
        value: Union[str, Dict, BaseModel],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            
        Returns:
            True if successful
        """
        client = await self.client
        
        if isinstance(value, BaseModel):
            value = value.model_dump_json()
        elif isinstance(value, dict):
            value = json.dumps(value)
        
        if ttl:
            return await client.setex(key, ttl, value)
        else:
            return await client.set(key, value)
    
    async def delete(self, key: str) -> int:
        """Delete a key from cache."""
        client = await self.client
        return await client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        client = await self.client
        return await client.exists(key) > 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on an existing key."""
        client = await self.client
        return await client.expire(key, ttl)
    
    async def incr(self, key: str) -> int:
        """Increment a counter."""
        client = await self.client
        return await client.incr(key)
    
    async def decr(self, key: str) -> int:
        """Decrement a counter."""
        client = await self.client
        return await client.decr(key)
    
    # =========================================================================
    # Hash Methods
    # =========================================================================
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get a field from a hash."""
        client = await self.client
        return await client.hget(name, key)
    
    async def hset(self, name: str, key: str, value: str) -> int:
        """Set a field in a hash."""
        client = await self.client
        return await client.hset(name, key, value)
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all fields from a hash."""
        client = await self.client
        return await client.hgetall(name)
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete fields from a hash."""
        client = await self.client
        return await client.hdel(name, *keys)
    
    # =========================================================================
    # List Methods (for queues)
    # =========================================================================
    
    async def lpush(self, key: str, *values: str) -> int:
        """Push values to the left of a list."""
        client = await self.client
        return await client.lpush(key, *values)
    
    async def rpush(self, key: str, *values: str) -> int:
        """Push values to the right of a list."""
        client = await self.client
        return await client.rpush(key, *values)
    
    async def lpop(self, key: str) -> Optional[str]:
        """Pop a value from the left of a list."""
        client = await self.client
        return await client.lpop(key)
    
    async def rpop(self, key: str) -> Optional[str]:
        """Pop a value from the right of a list."""
        client = await self.client
        return await client.rpop(key)
    
    async def blpop(
        self,
        keys: List[str],
        timeout: int = 0
    ) -> Optional[tuple]:
        """Blocking pop from the left of a list."""
        client = await self.client
        return await client.blpop(keys, timeout=timeout)
    
    async def llen(self, key: str) -> int:
        """Get the length of a list."""
        client = await self.client
        return await client.llen(key)
    
    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get a range of elements from a list."""
        client = await self.client
        return await client.lrange(key, start, end)
    
    # =========================================================================
    # Distributed Locking
    # =========================================================================
    
    async def acquire_lock(
        self,
        lock_name: str,
        timeout: int = 10,
        blocking: bool = True,
        blocking_timeout: Optional[int] = None
    ) -> Optional[redis.lock.Lock]:
        """
        Acquire a distributed lock.
        
        Args:
            lock_name: Name of the lock
            timeout: Lock expiration time in seconds
            blocking: Whether to block waiting for the lock
            blocking_timeout: How long to wait for the lock
            
        Returns:
            Lock object if acquired, None otherwise
        """
        client = await self.client
        lock = client.lock(
            lock_name,
            timeout=timeout,
            blocking=blocking,
            blocking_timeout=blocking_timeout
        )
        
        acquired = await lock.acquire()
        if acquired:
            self.logger.debug("Lock acquired", lock_name=lock_name)
            return lock
        
        self.logger.debug("Failed to acquire lock", lock_name=lock_name)
        return None
    
    async def release_lock(self, lock: redis.lock.Lock) -> None:
        """Release a distributed lock."""
        try:
            await lock.release()
            self.logger.debug("Lock released")
        except redis.exceptions.LockError:
            self.logger.warning("Lock already released or expired")
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    async def ping(self) -> bool:
        """Check if Redis is available."""
        try:
            client = await self.client
            return await client.ping()
        except Exception:
            return False
    
    async def flushdb(self) -> bool:
        """Flush the current database (use with caution!)."""
        client = await self.client
        return await client.flushdb()
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern."""
        client = await self.client
        return await client.keys(pattern)


# Singleton instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get the singleton Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
