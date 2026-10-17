from fastapi import APIRouter
from pydantic import BaseModel

from .auth import authenticate

router = APIRouter(prefix="/auth", tags=["authentication"])


class AuthenticationRequest(BaseModel):
    username: str
    password: str


@router.post("/authenticate")
def authenticate_user(request: AuthenticationRequest):
    return authenticate(request.username, request.password)