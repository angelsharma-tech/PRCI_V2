"""
Session Model for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import uuid
import json

from .base import BaseModel


class UserSession(BaseModel):
    """
    User session model for tracking user interactions
    """
    __tablename__ = "user_sessions"
    
    # Session identification
    session_id = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique session identifier"
    )
    
    # User relationship
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="Associated user ID"
    )
    
    # Session metadata
    user_agent = Column(
        Text,
        nullable=True,
        comment="User agent string"
    )
    
    ip_address = Column(
        String(45),
        nullable=True,
        comment="User IP address"
    )
    
    # Session state
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Session active status"
    )
    
    # Session data (JSON)
    session_data = Column(
        Text,
        nullable=True,
        comment="Session data in JSON format"
    )
    
    # Streamlit specific data
    streamlit_session_state = Column(
        Text,
        nullable=True,
        comment="Streamlit session state data"
    )
    
    # Timestamps
    expires_at = Column(
        DateTime,
        nullable=False,
        comment="Session expiration time"
    )
    
    last_activity_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Last activity timestamp"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="sessions"
    )
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, session_id={self.session_id}, user_id={self.user_id})>"
    
    @classmethod
    def create_session(cls, session, user_id: int, user_agent: str = None, 
                     ip_address: str = None, expires_hours: int = 24):
        """Create a new user session"""
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        user_session = cls(
            session_id=session_id,
            user_id=user_id,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            last_activity_at=datetime.utcnow()
        )
        
        session.add(user_session)
        session.commit()
        return user_session
    
    @classmethod
    def find_by_session_id(cls, session, session_id: str):
        """Find session by session ID"""
        return session.query(cls).filter(
            cls.session_id == session_id,
            cls.is_active == True,
            cls.expires_at > datetime.utcnow()
        ).first()
    
    @classmethod
    def find_active_sessions(cls, session, user_id: int):
        """Find all active sessions for a user"""
        return session.query(cls).filter(
            cls.user_id == user_id,
            cls.is_active == True,
            cls.expires_at > datetime.utcnow()
        ).all()
    
    @classmethod
    def cleanup_expired_sessions(cls, session):
        """Clean up expired sessions"""
        expired_count = session.query(cls).filter(
            cls.expires_at <= datetime.utcnow()
        ).delete()
        session.commit()
        return expired_count
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity_at = datetime.utcnow()
    
    def extend_session(self, hours: int = 24):
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def deactivate(self):
        """Deactivate session"""
        self.is_active = False
    
    def set_session_data(self, data: dict):
        """Store session data as JSON"""
        self.session_data = json.dumps(data) if data else None
    
    def get_session_data(self) -> dict:
        """Get session data as dictionary"""
        if self.session_data:
            try:
                return json.loads(self.session_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_streamlit_state(self, state_data: dict):
        """Store Streamlit session state"""
        if state_data:
            self.streamlit_session_state = json.dumps(state_data)
    
    def get_streamlit_state(self) -> dict:
        """Get Streamlit session state"""
        if self.streamlit_session_state:
            try:
                return json.loads(self.streamlit_session_state)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if session is valid and active"""
        return self.is_active and not self.is_expired()
    
    def to_safe_dict(self) -> dict:
        """Convert to dictionary excluding sensitive information"""
        data = self.to_dict(exclude_fields=['user_agent', 'ip_address'])
        return data
