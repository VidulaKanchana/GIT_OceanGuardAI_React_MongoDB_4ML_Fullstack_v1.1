from typing import Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    email: str
    full_name: str
    role: str = "fisherman"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class UserResponse(UserBase):
    user_id: str
    is_active: bool
    created_at: str
