from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
try:
    from pydantic import EmailStr  # type: ignore
    # ensure email-validator is available otherwise prefer a plain string
    try:
        import email_validator  # type: ignore
    except Exception:  # pragma: no cover - fallback for test envs
        EmailStr = str
except Exception:
    EmailStr = str
from fastapi.security import OAuth2PasswordRequestForm

from app.database.session import get_db
from app.models.user import User
from app.schemas.users import UserCreate, SocialLogin, OTPVerify
from app.auths.otp import create_otp_for_user, verify_otp_for_user
from app.auths.hashing import hash_password, verify_password
from app.auths.tokens import generate_token, verify_token
from app.auths.jwt import create_access_token
from app.services.email import send_email
from app.utils.security import get_current_user
from app.auths.oauth import verify_google_token, verify_github_token, exchange_google_code, exchange_github_code
from app.config import settings
from app.schemas.users import GoogleLogin, GitHubLogin
from app.schemas.users import GoogleCode, GitHubCode
from app.utils.logger import logger as base_logger

# Bound logger with context
logger = base_logger.bind(context="auth")

router = APIRouter(prefix="/auth", tags=["Auth"])

# -------------------------------
# REGISTER
# -------------------------------
@router.post("/register")
def register(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
    # Send verification email (background)
    token = generate_token(user.email)
    background_tasks.add_task(send_email, user.email, "Verify Your Account", f"http://localhost:3000/verify?token={token}")

    # Create OTP for 2FA / verification and send via BackgroundTasks
    otp = create_otp_for_user(db, new_user)
    background_tasks.add_task(send_email, new_user.email, "Your verification code", f"Your code is: {otp.code}")
    logger.info("Verification tasks scheduled", user_id=new_user.id)

    return {"message": "Registration successful. Check email for a verification code and link."}


@router.post("/verify-otp")
def verify_otp(payload: OTPVerify, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        logger.warning("OTP verification failed: user not found", email=payload.email)
        raise HTTPException(status_code=404, detail="User not found")

    ok = verify_otp_for_user(db, user, payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    user.is_verified = True
    db.commit()
    logger.info("User verified via OTP", user_id=user.id, email=user.email)
    return {"message": "Account verified"}


@router.post("/social-login")
def social_login(payload: SocialLogin, db: Session = Depends(get_db)):
    """A lightweight social login endpoint. In production verify provider tokens.
    Accepts provider, provider_id, and optional email. If user exists, returns token; otherwise creates one."""
    logger.info("Social login attempt", provider=payload.provider, provider_id=payload.provider_id, email=payload.email)
    user = None
    if payload.email:
        user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        # Create user (no password) and mark verified
        new_user = User(email=payload.email or f"{payload.provider_id}@{payload.provider}.local", password_hash="", is_verified=True)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
        logger.info("Created user via social login", user_id=user.id, email=user.email)

    token = create_access_token({"sub": user.email})
    logger.info("Social login successful", user_id=user.id, email=user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/social/google")
def social_google(payload: GoogleLogin, db: Session = Depends(get_db)):
    try:
        data = verify_google_token(payload.id_token)
    except Exception as exc:
        logger.warning("Google token verification failed", error=str(exc))
        raise HTTPException(status_code=400, detail="Invalid Google token")

    provider_id = data.get("sub")
    email = data.get("email")

    user = None
    if provider_id:
        user = db.query(User).filter(User.google_id == provider_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(email=email or f"{provider_id}@google.local", password_hash="", is_verified=True, google_id=provider_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created user via Google login", user_id=user.id, email=user.email)
    else:
        # ensure google_id set
        if not user.google_id:
            user.google_id = provider_id
            db.commit()

    token = create_access_token({"sub": user.email})
    logger.info("Google login successful", user_id=user.id, email=user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/social/google/code")
def social_google_code(payload: GoogleCode, db: Session = Depends(get_db)):
    try:
        data = exchange_google_code(payload.code, payload.redirect_uri)
    except Exception as exc:
        logger.warning("Google code exchange failed", error=str(exc))
        raise HTTPException(status_code=400, detail="Invalid Google code")

    provider_id = data.get("sub")
    email = data.get("email")

    user = None
    if provider_id:
        user = db.query(User).filter(User.google_id == provider_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(email=email or f"{provider_id}@google.local", password_hash="", is_verified=True, google_id=provider_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created user via Google code login", user_id=user.id, email=user.email)
    else:
        if not user.google_id:
            user.google_id = provider_id
            db.commit()

    token = create_access_token({"sub": user.email})
    logger.info("Google code login successful", user_id=user.id, email=user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/social/github/code")
def social_github_code(payload: GitHubCode, db: Session = Depends(get_db)):
    try:
        data = exchange_github_code(payload.code)
    except Exception as exc:
        logger.warning("GitHub code exchange failed", error=str(exc))
        raise HTTPException(status_code=400, detail="Invalid GitHub code")

    provider_id = str(data.get("id"))
    email = data.get("email")

    user = None
    if provider_id:
        user = db.query(User).filter(User.github_id == provider_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(email=email or f"{provider_id}@github.local", password_hash="", is_verified=True, github_id=provider_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created user via GitHub code login", user_id=user.id, email=user.email)
    else:
        if not user.github_id:
            user.github_id = provider_id
            db.commit()

    token = create_access_token({"sub": user.email})
    logger.info("GitHub code login successful", user_id=user.id, email=user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/social/github")
def social_github(payload: GitHubLogin, db: Session = Depends(get_db)):
    try:
        data = verify_github_token(payload.access_token)
    except Exception as exc:
        logger.warning("GitHub token verification failed", error=str(exc))
        raise HTTPException(status_code=400, detail="Invalid GitHub token")

    provider_id = str(data.get("id"))
    email = data.get("email")

    user = None
    if provider_id:
        user = db.query(User).filter(User.github_id == provider_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(email=email or f"{provider_id}@github.local", password_hash="", is_verified=True, github_id=provider_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created user via GitHub login", user_id=user.id, email=user.email)
    else:
        if not user.github_id:
            user.github_id = provider_id
            db.commit()

    token = create_access_token({"sub": user.email})
    logger.info("GitHub login successful", user_id=user.id, email=user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get('/oauth-config')
def oauth_config():
    # expose client IDs for building auth URLs on the client side (no secrets)
    return {
        'google_client_id': settings.GOOGLE_CLIENT_ID,
        'github_client_id': settings.GITHUB_CLIENT_ID,
        'google_auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'github_auth_url': 'https://github.com/login/oauth/authorize'
    }

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
