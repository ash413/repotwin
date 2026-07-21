import stripe
from app.config import STRIPE_API_KEY
from app.tasks.worker import send_receipt_email

stripe.api_key = STRIPE_API_KEY


class PaymentService:
    """Wraps Stripe PaymentIntents for checkout."""

    def charge(self, amount_cents: int, currency: str, customer_id: str):
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            customer=customer_id,
        )
        send_receipt_email.delay(customer_id, amount_cents)
        return intent
