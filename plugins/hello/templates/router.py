from fastapi import APIRouter

from .hello import greet

router = APIRouter(prefix="/hello", tags=["hello"])


@router.get("/")
def hello():
    return {"message": greet()}