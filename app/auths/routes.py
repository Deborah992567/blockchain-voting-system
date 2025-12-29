from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import EmailStr
from fastapi.security import OAuth2PasswordRequestForm

from app.database.session import get_db
from app.models.user import User
from app.schemas.users import UserCreate
from app.auths.hashing import hash_password, verify_password
from app.auths.tokens import generate_token, verify_token
from app.auths.jwt import create_access_token
from app.services.email import send_email
from app.utils.security import get_current_user
from app.utils.logger import logger as base_logger

# Bound logger with context
logger = base_logger.bind(context="auth")

router = APIRouter(prefix="/auth", tags=["Auth"])

# -------------------------------
# REGISTER
# -------------------------------
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    logger.info("Registration attempt", email=user.email)
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        logger.warning("Registration failed: email already exists", email=user.email)
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed = hash_password(user.password)
    new_user = User(email=user.email, password_hash=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info("User created", user_id=new_user.id, email=new_user.email)

    # Send verification email
    token = generate_token(user.email)
    try:
        send_email(
            user.email,
            "Verify Your Account",
            f"http://localhost:3000/verify?token={token}"
        )
        logger.info("Verification email sent", email=user.email)
    except Exception:
        logger.exception("Failed to send verification email", email=user.email)

    return {"message": "Registration successful. Check email to verify account."}

# -------------------------------
# EMAIL VERIFICATION
# -------------------------------
@router.get("/verify")
def verify_email(token: str, db: Session = Depends(get_db)):
    logger.info("Email verification attempt")
    try:
        email = verify_token(token)
    except Exception:
        logger.warning("Invalid or expired verification token")
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.warning("Verification failed: user not found", email=email)
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.commit()
    logger.info("Email verified", email=email)
    return {"message": "Email verified successfully."}

# -------------------------------
# LOGIN
# -------------------------------
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info("Login attempt", email=form_data.username)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning("Login failed: invalid credentials", email=form_data.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_verified:
        logger.warning("Login failed: email not verified", email=form_data.username)
        raise HTTPException(status_code=403, detail="Verify your email first")

    token = create_access_token({"sub": user.email})
    logger.info("Login successful", email=user.email)
    return {"access_token": token, "token_type": "bearer"}

# -------------------------------
# FORGOT PASSWORD
# -------------------------------
@router.post("/forgot-password")
def forgot_password(email: EmailStr, db: Session = Depends(get_db)):
    logger.info("Forgot password requested", email=email)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.info("Forgot password: email not found (silent)", email=email)
        # Don't reveal if user exists
        return {"message": "If email exists, reset link sent"}

    token = generate_token(email)
    try:
        send_email(
            email,
            "Reset Password",
            f"http://localhost:3000/reset?token={token}"
        )
        logger.info("Password reset email sent", email=email)
    except Exception:
        logger.exception("Failed to send password reset email", email=email)

    return {"message": "If email exists, reset link sent"}

# -------------------------------
# RESET PASSWORD
# -------------------------------
@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    logger.info("Password reset attempt")
    try:
        email = verify_token(token)
    except Exception:
        logger.warning("Invalid or expired password reset token")
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.warning("Password reset failed: user not found", email=email)
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(new_password)
    db.commit()
    logger.info("Password updated", email=email)
    return {"message": "Password updated successfully."}

# -------------------------------
# TEST PROTECTED ROUTE
# -------------------------------
@router.get("/me")
def me(user = Depends(get_current_user)):
    logger.info("Accessed protected /me", email=user.email)
    return {
        "email": user.email,
        "role": user.role,
        "is_verified": user.is_verified
    }
