from fastapi import FastAPI
from app.routes import auth_routes, checkout_routes, product_routes

app = FastAPI(title="Demo E-Commerce API")

app.include_router(auth_routes.router)
app.include_router(checkout_routes.router)
app.include_router(product_routes.router)


@app.get("/health")
def health():
    return {"status": "ok"}
