"""
backend/routers/auth.py
POST /auth/login -- no JWT issued. See PRD Section 10.1 and Section 14.
"""
from fastapi import APIRouter

from backend.models.schemas import LoginRequest, LoginResponse, UserPublic
from backend.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user = auth_service.authenticate(payload.username, payload.password)
    if user is None:
        return LoginResponse(success=False, error="Invalid credentials")
    return LoginResponse(success=True, user=UserPublic(**user))
