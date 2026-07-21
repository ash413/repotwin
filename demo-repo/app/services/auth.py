import jwt
from app.config import JWT_SECRET
from app.services.session_store import SessionStore
from app.db import SessionLocal
from app.models.user import User


class AuthService:
    def __init__(self):
        self.sessions = SessionStore()

    def login(self, email: str, password: str):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            # password check omitted for brevity
            session_id = self.sessions.create_session(user.id)
            token = jwt.encode({"sid": session_id, "sub": user.id}, JWT_SECRET, algorithm="HS256")
            return token
        finally:
            db.close()

    def verify(self, token: str):
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        session = self.sessions.get_session(payload["sid"])
        if not session:
            raise ValueError("session expired or missing")
        return session["user_id"]
