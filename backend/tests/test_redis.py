import pytest
import warnings

from app.redis import redis_pool, get_redis

@pytest.fixture(autouse=True)
def ignore_warnings():
    warnings.simplefilter("ignore")

@pytest.mark.asyncio
async def test_redis_connection():
    """
    Test that the application can successfully connect to the Redis database.
    """
    try:
        # Create a generator and get the next item which is the redis client
        client_generator = get_redis()
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
    finally:
        await redis_pool.disconnect()

@pytest.mark.asyncio
async def test_redis_set_get():
    """
    Test basic SET and GET operations on Redis.
    """
    try:
        client_generator = get_redis()
        client = await anext(client_generator)
        
        await client.set("test_key", "test_value", ex=10) # Set key with expiration of 10s
        value = await client.get("test_key")
        
        assert value == "test_value"
        
        # Cleanup
        try:
            await anext(client_generator)
        except StopAsyncIteration:
            pass
            
    except Exception as e:
        pytest.fail(f"Redis set/get operations failed: {e}")
    finally:
        await redis_pool.disconnect()
