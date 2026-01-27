import time
import redis.asyncio as redis
from typing import Optional
from loguru import logger
from genpulse import config

class RateLimiter:
    """
    Distributed Rate Limiter using Redis.
    Implements a Token Bucket algorithm via Lua script for atomicity.
    """
    
    # Lua script for token bucket
    # Keys: [rate_limit_key]
    # Args: [capacity, tokens_per_sec, timestamp]
    # Returns: [allowed (0/1), remaining_tokens]
    _LUA_SCRIPT = """
    local key = KEYS[1]
    local capacity = tonumber(ARGV[1])
    local rate = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])
    
    local last_tokens = tonumber(redis.call("HGET", key, "tokens"))
    local last_refreshed = tonumber(redis.call("HGET", key, "last_refreshed"))
    
    if last_tokens == nil then
        last_tokens = capacity
        last_refreshed = now
    end
    
    -- Calculate refilled tokens
    local delta = math.max(0, now - last_refreshed)
    local filled = last_tokens + (delta * rate)
    
    if filled > capacity then
        filled = capacity
    end
    
    local allowed = 0
    if filled >= 1.0 then
        allowed = 1
        filled = filled - 1.0
        -- Only update timestamp if we consumed a token
        redis.call("HSET", key, "tokens", filled, "last_refreshed", now)
        -- Set expiry to avoid stale keys (e.g., 1 hour)
        redis.call("EXPIRE", key, 3600)
    else
        -- Just update timestamp/tokens to current state logic if needed, 
        -- but for GCRA pure we mostly update on consume. 
        -- Here we update to keep state fresh.
        redis.call("HSET", key, "tokens", filled, "last_refreshed", now)
        redis.call("EXPIRE", key, 3600)
    end
    
    return {allowed, filled}
    """

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or config.REDIS_URL
        self.client = redis.from_url(self.redis_url, decode_responses=True)
        self.script_sha = None

    async def _ensure_script(self):
        if not self.script_sha:
            self.script_sha = await self.client.script_load(self._LUA_SCRIPT)

    async def acquire(self, key: str, limit_per_sec: float) -> bool:
        """
        Attempt to acquire a token.
        :param key: Unique identifier (e.g., "rate:provider:tencent")
        :param limit_per_sec: Rate limit (e.g., 0.5 for 1 request every 2 seconds, or 5 for 5 req/s)
        :return: True if allowed, False if limited
        """
        await self._ensure_script()
        
        # Capacity usually equals limit for simple burst handling, or limit * burst_seconds
        capacity = max(1.0, limit_per_sec) 
        
        try:
            result = await self.client.evalsha(
                self.script_sha, 
                1, 
                f"genpulse:ratelimit:{key}", 
                capacity, 
                limit_per_sec, 
                time.time()
            )
            return bool(result[0])
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # If Redis fails, fail open or closed? 
            # Fail closed (False) protects the API, Fail open (True) prioritizes availability.
            # Let's fail open to minimize impact of Redis blips on internal flow, 
            # BUT log heavily.
            return True

    async def close(self):
        await self.client.aclose()
