import json
import uuid
from app.services.cache import get_redis

SESSION_TTL_SECONDS = 60 * 60 * 24  # 24h


class SessionStore:
    """User session state, backed entirely by Redis.

    If Redis is unavailable, logged-in users are silently signed out on
    their next request because create_session/get_session both fail.
    """

    def __init__(self):
        self.redis = get_redis()

    def create_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        self.redis.setex(
            f"session:{session_id}",
            SESSION_TTL_SECONDS,
            json.dumps({"user_id": user_id}),
        )
        return session_id

    def get_session(self, session_id: str):
        raw = self.redis.get(f"session:{session_id}")
        return json.loads(raw) if raw else None

    def destroy_session(self, session_id: str):
        self.redis.delete(f"session:{session_id}")
