from fastapi import APIRouter, HTTPException
from app.services.product_cache import ProductCache

router = APIRouter(prefix="/products")
product_cache = ProductCache()


@router.get("/{product_id}")
def get_product(product_id: str):
    product = product_cache.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="product not found")
    return product
