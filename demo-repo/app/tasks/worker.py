from celery import Celery
from app.config import CELERY_BROKER_URL

celery_app = Celery("demo_app", broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL)


@celery_app.task
def send_receipt_email(customer_id: str, amount_cents: int):
    # In production this would call an email provider.
    print(f"Sending receipt to {customer_id} for {amount_cents} cents")


@celery_app.task
def sync_inventory_levels():
    # Periodic job, scheduled via celery beat, reads/writes product cache.
    print("Syncing inventory levels")
