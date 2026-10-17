from fastapi import APIRouter

from .service import get_message

router = APIRouter(prefix="/welcome", tags=["welcome"])


@router.get("/")
def get_greeting():
    return {"message": get_message()}
