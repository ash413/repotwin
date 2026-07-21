from fastapi import APIRouter, Request, HTTPException
from app.services.payments import PaymentService
from app.services.rate_limiter import RateLimiter
from app.services.product_cache import ProductCache

router = APIRouter(prefix="/checkout")
payments = PaymentService()
rate_limiter = RateLimiter()
product_cache = ProductCache()


@router.post("/charge")
def charge(request: Request, product_id: str, customer_id: str):
    if not rate_limiter.is_allowed(request.client.host):
        raise HTTPException(status_code=429, detail="rate limit exceeded")

    product = product_cache.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="product not found")

    intent = payments.charge(product["price_cents"], "usd", customer_id)
    return {"client_secret": intent.client_secret}
