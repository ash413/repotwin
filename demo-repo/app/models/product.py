from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base
from app.db import SessionLocal

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    price_cents = Column(Integer, nullable=False)


def get_product_from_db(product_id: str):
    db = SessionLocal()
    try:
        row = db.query(Product).filter(Product.id == product_id).first()
        if not row:
            return None
        return {"id": row.id, "name": row.name, "price_cents": row.price_cents}
    finally:
        db.close()
