import time
from app.services.cache import get_redis

WINDOW_SECONDS = 60
MAX_REQUESTS = 100


class RateLimiter:
    """Sliding-window rate limiter using Redis sorted sets.

    Without Redis, this raises on every call. api_gateway.middleware
    treats that as fail-open (allows the request) but logs an error,
    meaning rate limiting silently disappears if Redis is down.
    """

    def __init__(self):
        self.redis = get_redis()

    def is_allowed(self, client_key: str) -> bool:
        now = time.time()
        window_start = now - WINDOW_SECONDS
        key = f"ratelimit:{client_key}"

        self.redis.zremrangebyscore(key, 0, window_start)
        count = self.redis.zcard(key)
        if count >= MAX_REQUESTS:
            return False

        self.redis.zadd(key, {str(now): now})
        self.redis.expire(key, WINDOW_SECONDS)
        return True
