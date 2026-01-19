import pytest
from unittest.mock import AsyncMock, patch

# We import inside test functions or check for import error because module might not exist yet
# But actually standard TDD says create test file first.

@pytest.mark.asyncio
async def test_redis_connection():
    # We will mock the redis.from_url to return an AsyncMock
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        mock_client.ping.return_value = True

        from core.mq import RedisManager
        redis_mgr = RedisManager()
        result = await redis_mgr.ping()
        
        assert result is True
        mock_client.ping.assert_called_once()
