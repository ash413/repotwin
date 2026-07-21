from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    stripe_payment_intent_id = Column(String, nullable=True)
    status = Column(String, default="pending")
