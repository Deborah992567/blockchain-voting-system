from pydantic import BaseModel
from importlib import util as _importlib_util

# If the optional `email_validator` package is not installed, avoid using
# pydantic's EmailStr type because schema generation will attempt to import
# the validator and fail during test collection; fall back to `str`.
if _importlib_util.find_spec("email_validator") is None:
    EmailStr = str
else:
    from pydantic import EmailStr  # type: ignore
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_verified: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class SocialLogin(BaseModel):
    provider: str
    provider_id: str
    email: Optional[EmailStr] = None


class GoogleLogin(BaseModel):
    id_token: str


class GitHubLogin(BaseModel):
    access_token: str


class GoogleCode(BaseModel):
    code: str
    redirect_uri: str


class GitHubCode(BaseModel):
    code: str


class OTPVerify(BaseModel):
    email: EmailStr
    code: str
