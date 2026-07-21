import json
from app.services.cache import get_redis
from app.models.product import get_product_from_db

CACHE_TTL_SECONDS = 300


class ProductCache:
    """Read-through cache in front of PostgreSQL for product lookups."""

    def __init__(self):
        self.redis = get_redis()

    def get_product(self, product_id: str):
        cached = self.redis.get(f"product:{product_id}")
        if cached:
            return json.loads(cached)

        product = get_product_from_db(product_id)
        if product:
            self.redis.setex(
                f"product:{product_id}", CACHE_TTL_SECONDS, json.dumps(product)
            )
        return product
