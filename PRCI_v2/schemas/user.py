"""
User Schemas for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr, ConfigDict

from models.user import UserStatus, UserRole


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr = Field(description="User email address")
    username: Optional[str] = Field(default=None, max_length=100, description="Username")
    first_name: Optional[str] = Field(default=None, max_length=100, description="First name")
    last_name: Optional[str] = Field(default=None, max_length=100, description="Last name")
    bio: Optional[str] = Field(default=None, description="User biography")
    timezone: str = Field(default="UTC", description="User timezone")
    language: str = Field(default="en", description="User language")
    
    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(min_length=8, description="User password")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    status: UserStatus = Field(default=UserStatus.PENDING, description="User status")
    share_data: bool = Field(default=False, description="Data sharing consent")
    email_notifications: bool = Field(default=True, description="Email notification preference")


class UserUpdate(BaseModel):
    """User update schema"""
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    username: Optional[str] = Field(default=None, max_length=100)
    bio: Optional[str] = Field(default=None)
    timezone: Optional[str] = Field(default=None)
    language: Optional[str] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None)
    preferences: Optional[Dict[str, Any]] = Field(default=None)
    share_data: Optional[bool] = Field(default=None)
    email_notifications: Optional[bool] = Field(default=None)
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """User response schema"""
    id: int = Field(description="User ID")
    full_name: Optional[str] = Field(default=None, description="Full name")
    is_verified: bool = Field(description="Email verification status")
    status: UserStatus = Field(description="Account status")
    role: UserRole = Field(description="User role")
    avatar_url: Optional[str] = Field(default=None, description="Avatar URL")
    share_data: bool = Field(description="Data sharing consent")
    email_notifications: bool = Field(description="Email notifications")
    last_login_at: Optional[datetime] = Field(default=None, description="Last login")
    email_verified_at: Optional[datetime] = Field(default=None, description="Email verified at")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    
    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(UserResponse):
    """Extended user profile response"""
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences")
    total_assessments: int = Field(default=0, description="Total assessments")
    total_conversations: int = Field(default=0, description="Total conversations")
    total_interventions: int = Field(default=0, description="Total interventions")
    total_reports: int = Field(default=0, description="Total reports")
    
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """User list response"""
    id: int
    email: str
    username: Optional[str]
    full_name: Optional[str]
    status: UserStatus
    role: UserRole
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class UserStatusUpdate(BaseModel):
    """User status update request"""
    status: UserStatus = Field(description="New status")


class UserRoleUpdate(BaseModel):
    """User role update request"""
    role: UserRole = Field(description="New role")


class UserPreferencesUpdate(BaseModel):
    """User preferences update"""
    preferences: Dict[str, Any] = Field(description="Updated preferences")


class UserStatistics(BaseModel):
    """User statistics"""
    total_users: int = Field(description="Total users")
    active_users: int = Field(description="Active users")
    new_users_today: int = Field(description="New users today")
    new_users_week: int = Field(description="New users this week")
    new_users_month: int = Field(description="New users this month")
    users_by_status: Dict[str, int] = Field(description="Users by status")
    users_by_role: Dict[str, int] = Field(description="Users by role")
