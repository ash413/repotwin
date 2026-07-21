import redis
from app.config import REDIS_URL

# Single shared Redis connection used across the app for:
# - session storage (app.services.session_store)
# - rate limiting (app.services.rate_limiter)
# - response caching (app.services.product_cache)
# - Celery broker (app.tasks.worker)
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_redis():
    return redis_client
