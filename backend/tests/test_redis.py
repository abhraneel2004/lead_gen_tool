import pytest
import warnings

from redis import asyncio as aioredis
from app.config import settings
import app.redis

@pytest.fixture(autouse=True)
def ignore_warnings():
    warnings.simplefilter("ignore")

@pytest.fixture(scope="function", autouse=True)
async def cleanup_redis_pool():
    # Setup - Recreate the pool so it binds to the current test's event loop
    app.redis.redis_pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
    )
    yield
    # Teardown - disconnect the pool after the test loop finishes
    await app.redis.redis_pool.disconnect()

@pytest.mark.asyncio
async def test_redis_connection():
    """
    Test that the application can successfully connect to the Redis database.
    """
    try:
        # Create a generator and get the next item which is the redis client
        client_generator = app.redis.get_redis()
        client = await anext(client_generator)
        
        # Ping the redis server
        response = await client.ping()
        assert response is True
        
        # Cleanup
        try:
            await anext(client_generator)
        except StopAsyncIteration:
            pass
            
    except Exception as e:
        pytest.fail(f"Redis connection failed: {e}")

@pytest.mark.asyncio
async def test_redis_set_get():
    """
    Test basic SET and GET operations on Redis.
    """
    test_key = "test_lead_scraper_key"
    try:
        client_generator = app.redis.get_redis()
        client = await anext(client_generator)
        
        await client.set(test_key, "test_value", ex=10) # Set key with expiration of 10s
        value = await client.get(test_key)
        
        assert value == "test_value"
        
        # Explicitly delete the key so it does not pollute the database
        await client.delete(test_key)
        
        # Cleanup connection generator
        try:
            await anext(client_generator)
        except StopAsyncIteration:
            pass
            
    except Exception as e:
        pytest.fail(f"Redis set/get operations failed: {e}")
