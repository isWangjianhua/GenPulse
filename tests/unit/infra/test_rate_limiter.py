import pytest
from unittest.mock import AsyncMock, MagicMock
from genpulse.infra.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_acquire_allowed(mocker):
    """Test successful token acquisition (Mocked)."""
    # Arrange
    mocker.patch("redis.asyncio.from_url")
    limiter = RateLimiter()
    limiter.client = AsyncMock()
    # Mock script load
    limiter.client.script_load.return_value = "sha123"
    # Mock evalsha returning [1, 5.0] (allowed, 5 tokens left)
    limiter.client.evalsha.return_value = [1, 5.0]

    # Act
    allowed = await limiter.acquire("test_key", 10.0)

    # Assert
    assert allowed is True
    limiter.client.evalsha.assert_called_once()
    args = limiter.client.evalsha.call_args
    assert args[0][0] == "sha123" # script sha
    assert args[0][1] == 1 # num keys (KEYS[1])
    assert args[0][2] == "genpulse:ratelimit:test_key"

@pytest.mark.asyncio
async def test_rate_limiter_acquire_denied(mocker):
    """Test rate limit exceeded (Mocked)."""
    mocker.patch("redis.asyncio.from_url")
    limiter = RateLimiter()
    limiter.client = AsyncMock()
    limiter.client.script_load.return_value = "sha123"
    # Mock evalsha returning [0, 0.0] (denied, 0 tokens)
    limiter.client.evalsha.return_value = [0, 0.0]

    # Act
    allowed = await limiter.acquire("test_key", 1.0)

    # Assert
    assert allowed is False
