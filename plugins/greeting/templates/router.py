from fastapi import APIRouter

from .service import get_message

router = APIRouter(prefix="/greeting", tags=["greeting"])


@router.get("/")
def get_greeting():
    return {"message": get_message()}
