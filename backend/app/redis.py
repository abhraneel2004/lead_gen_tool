"""
Redis client connection and utilities.
"""

import logging
from typing import AsyncGenerator

from redis import asyncio as aioredis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)

# Create a Redis connection pool using the settings URL
redis_pool = aioredis.ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=settings.REDIS_MAX_CONNECTIONS,
)

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    FastAPI dependency that yields a Redis client from the connection pool.
    Includes error handling for Redis connection issues.
    """
    client = aioredis.Redis(connection_pool=redis_pool)
    try:
        # We can ping to ensure the connection is active if needed, but the pool handles most of it.
        yield client
    except RedisError as e:
        logger.error(f"Redis connection error: {e}")
        raise
    finally:
        await client.aclose()
