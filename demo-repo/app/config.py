import os

# --- Core infra connection strings (env-driven) ---
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/appdb")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_xxx")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
