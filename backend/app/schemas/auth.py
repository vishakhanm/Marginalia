from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    auth_provider: str
    created_at: datetime