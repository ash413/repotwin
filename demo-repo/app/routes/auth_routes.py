from fastapi import APIRouter
from app.services.auth import AuthService

router = APIRouter(prefix="/auth")
auth_service = AuthService()


@router.post("/login")
def login(email: str, password: str):
    token = auth_service.login(email, password)
    return {"token": token}


@router.post("/verify")
def verify(token: str):
    user_id = auth_service.verify(token)
    return {"user_id": user_id}
