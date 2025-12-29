from fastapi import Depends, HTTPException
from app.utils.security import get_current_user
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="admin")

def admin_only(user = Depends(get_current_user)):
    if user.role != "admin":
        logger.warning("Admin only access denied", user_id=getattr(user, 'id', None))
        raise HTTPException(status_code=403, detail="Admin only")
    return user
