from pydantic import BaseModel, EmailStr
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


class OTPVerify(BaseModel):
    email: EmailStr
    code: str
