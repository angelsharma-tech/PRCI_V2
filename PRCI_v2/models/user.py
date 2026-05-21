"""
User Model for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class UserStatus(enum.Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserRole(enum.Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class User(BaseModel):
    """
    User model for storing user information
    """
    __tablename__ = "users"
    
    # Basic user information
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (unique identifier)"
    )
    
    username = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
        comment="Unique username"
    )
    
    first_name = Column(
        String(100),
        nullable=True,
        comment="User first name"
    )
    
    last_name = Column(
        String(100),
        nullable=True,
        comment="User last name"
    )
    
    full_name = Column(
        String(255),
        nullable=True,
        comment="User full name (display name)"
    )
    
    # Authentication fields (prepared for future auth system)
    password_hash = Column(
        String(255),
        nullable=True,
        comment="Hashed password (for future authentication)"
    )
    
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Email verification status"
    )
    
    # User status and role
    status = Column(
        Enum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False,
        comment="User account status"
    )
    
    role = Column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False,
        comment="User role"
    )
    
    # Profile information
    bio = Column(
        Text,
        nullable=True,
        comment="User biography"
    )
    
    avatar_url = Column(
        String(500),
        nullable=True,
        comment="Profile avatar URL"
    )
    
    timezone = Column(
        String(50),
        default="UTC",
        nullable=False,
        comment="User timezone"
    )
    
    language = Column(
        String(10),
        default="en",
        nullable=False,
        comment="User language preference"
    )
    
    # Preferences
    preferences = Column(
        Text,
        nullable=True,
        comment="User preferences in JSON format"
    )
    
    # Privacy settings
    share_data = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Consent to share anonymized data"
    )
    
    email_notifications = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Email notification preferences"
    )
    
    # Timestamps for specific events
    last_login_at = Column(
        DateTime,
        nullable=True,
        comment="Last login timestamp"
    )
    
    email_verified_at = Column(
        DateTime,
        nullable=True,
        comment="Email verification timestamp"
    )
    
    # Relationships
    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    assessments = relationship(
        "Assessment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    interventions = relationship(
        "UserIntervention",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    reports = relationship(
        "Report",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, status={self.status})>"
    
    @property
    def display_name(self) -> str:
        """Get user's display name"""
        if self.full_name:
            return self.full_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.username:
            return self.username
        else:
            return self.email
    
    @property
    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login_at = datetime.utcnow()
    
    def verify_email(self):
        """Mark email as verified"""
        self.is_verified = True
        self.email_verified_at = datetime.utcnow()
    
    def to_safe_dict(self) -> dict:
        """Convert to dictionary excluding sensitive information"""
        data = self.to_dict(exclude_fields=['password_hash'])
        return data
    
    @classmethod
    def find_by_email(cls, session, email: str):
        """Find user by email"""
        return session.query(cls).filter(cls.email == email).first()
    
    @classmethod
    def find_by_username(cls, session, username: str):
        """Find user by username"""
        return session.query(cls).filter(cls.username == username).first()
    
    @classmethod
    def find_active_users(cls, session):
        """Find all active users"""
        return session.query(cls).filter(cls.status == UserStatus.ACTIVE)
