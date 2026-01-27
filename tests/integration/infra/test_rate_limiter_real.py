import pytest
import asyncio
from genpulse.infra.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_real_redis():
    """
    Test generic token bucket behavior with real Redis.
    Requires local Redis running.
    """
    limiter = RateLimiter()
    key = "integration_test_limit"
    
    try:
        # Check connection first
        await limiter.client.ping()
    except Exception:
        pytest.skip("Redis not available")

    # Clear key first
    await limiter.client.delete(f"genpulse:ratelimit:{key}")

    # Set limit to 2 per second
    limit = 2.0
    
    # 1. Burst of 2 should pass
    assert await limiter.acquire(key, limit) is True
    assert await limiter.acquire(key, limit) is True
    
    # 2. 3rd should fail immediately
    assert await limiter.acquire(key, limit) is False
    
    # 3. Wait 0.6s (regenerates ~1.2 tokens) => Should pass
    await asyncio.sleep(0.6)
    assert await limiter.acquire(key, limit) is True
    
    await limiter.close()
