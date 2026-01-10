from passlib.context import CryptContext

# Use argon2 as primary hash method (no 72-byte limit like bcrypt)
try:
    pwd_context = CryptContext(
        schemes=["argon2"],
        deprecated="auto"
    )
except ImportError:
    # Fallback to bcrypt if argon2 not available
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using argon2 or bcrypt."""
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(password, hashed)
