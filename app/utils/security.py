from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.auths.jwt import decode_access_token
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="security")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        logger.warning("Invalid token or missing subject")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")
    email = payload["sub"]
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.warning("Authenticated user not found", email=email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user



def admin_only(user = Depends(get_current_user)):
    if user.role != "admin":
        logger.warning("Admin-only access denied", user_id=getattr(user, 'id', None))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user
