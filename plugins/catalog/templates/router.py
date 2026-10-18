from fastapi import APIRouter

from .service import get_message

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/")
def get_greeting():
    return {"message": get_message()}
