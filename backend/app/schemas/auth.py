"""Pydantic schemas for user registration, authentication, and session tokens."""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(description="User login email address")
    full_name: str = Field(min_length=2, max_length=255, description="Full name of user")
    password: str = Field(min_length=8, max_length=128, description="Plaintext password (min 8 chars)")
    role: str = Field(default="USER", description="Role: USER, REVIEWER, or ADMIN")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(description="User login email address")
    password: str = Field(min_length=1, max_length=128, description="User password")


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int
    user: UserResponse


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int
