import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.utils.logger import logger as base_logger
from app.models.otp import OTP
from app.models.user import User

logger = base_logger.bind(context="auth.otp")


def _generate_code(length: int = 6) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def create_otp_for_user(db: Session, user: User, ttl_seconds: int = 300) -> OTP:
    code = _generate_code()
    expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    otp = OTP(user_id=user.id, code=code, expires_at=expires_at)
    db.add(otp)
    db.commit()
    db.refresh(otp)
    logger.info("Created OTP for user", user_id=user.id, otp_id=otp.id)
    return otp


def verify_otp_for_user(db: Session, user: User, code: str) -> bool:
    now = datetime.utcnow()
    otp = db.query(OTP).filter(OTP.user_id == user.id, OTP.code == code, OTP.used == False).order_by(OTP.created_at.desc()).first()
    if not otp:
        logger.warning("OTP verify failed: code not found", user_id=user.id)
        return False
    if otp.expires_at < now:
        logger.warning("OTP verify failed: expired", user_id=user.id, otp_id=otp.id)
        return False
    otp.used = True
    db.commit()
    logger.info("OTP verified", user_id=user.id, otp_id=otp.id)
    return True


def cleanup_expired_otps(db: Session):
    now = datetime.utcnow()
    expired = db.query(OTP).filter(OTP.expires_at < now, OTP.used == False).all()
    count = len(expired)
    for o in expired:
        o.used = True
    db.commit()
    logger.info("Cleaned up expired OTPs", count=count)
