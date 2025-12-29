from fastapi import APIRouter, Depends
from app.utils.security import get_current_user

router = APIRouter(prefix="/test")

@router.get("/protected")
def protected(user = Depends(get_current_user)):
    return {
        "message": "You are authenticated",
        "email": user.email,
        "role": user.role
    }
