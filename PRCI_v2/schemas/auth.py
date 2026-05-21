"""
Authentication Schemas for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr, field_validator


class Token(BaseModel):
    """JWT token response"""
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")
    user_id: int = Field(description="User ID")
    email: str = Field(description="User email")


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: Optional[str] = Field(default=None, description="Subject (user ID)")
    email: Optional[str] = Field(default=None, description="User email")
    role: Optional[str] = Field(default=None, description="User role")
    exp: Optional[datetime] = Field(default=None, description="Expiration time")
    iat: Optional[datetime] = Field(default=None, description="Issued at time")
    jti: Optional[str] = Field(default=None, description="Token unique identifier")


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Remember login session")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "secure_password123",
                "remember_me": False
            }
        }


class RegisterRequest(BaseModel):
    """Registration request"""
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, description="User password (min 8 characters)")
    first_name: str = Field(min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(default=None, max_length=100, description="Last name")
    username: Optional[str] = Field(default=None, max_length=100, description="Username")
    timezone: str = Field(default="UTC", description="User timezone")
    language: str = Field(default="en", description="User language preference")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123",
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "timezone": "UTC",
                "language": "en"
            }
        }


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str = Field(description="Password reset token")
    new_password: str = Field(min_length=8, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str = Field(description="Current password")
    new_password: str = Field(min_length=8, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(description="Refresh token")


class LogoutRequest(BaseModel):
    """Logout request"""
    all_devices: bool = Field(default=False, description="Logout from all devices")
