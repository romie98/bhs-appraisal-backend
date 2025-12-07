"""Authentication Pydantic schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserSignup(BaseModel):
    """Schema for user signup"""
    full_name: str = Field(..., min_length=1, description="User's full name")
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class GoogleLogin(BaseModel):
    """Schema for Google OAuth login"""
    google_token: str = Field(..., description="Google ID token from OAuth")


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    full_name: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


