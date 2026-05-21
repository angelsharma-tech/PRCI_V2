"""
Conversation Model for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class ConversationStatus(enum.Enum):
    """Conversation status enumeration"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MessageRole(enum.Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(BaseModel):
    """
    Conversation model for storing chat sessions
    """
    __tablename__ = "conversations"
    
    # User relationship
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="Associated user ID"
    )
    
    # Conversation metadata
    title = Column(
        String(255),
        nullable=True,
        comment="Conversation title"
    )
    
    status = Column(
        Enum(ConversationStatus),
        default=ConversationStatus.ACTIVE,
        nullable=False,
        comment="Conversation status"
    )
    
    # Conversation context
    context_data = Column(
        Text,
        nullable=True,
        comment="Conversation context data in JSON format"
    )
    
    # Assessment data (link to assessment)
    current_assessment_id = Column(
        Integer,
        ForeignKey("assessments.id"),
        nullable=True,
        comment="Current assessment ID"
    )
    
    # Conversation statistics
    message_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total message count"
    )
    
    last_message_at = Column(
        DateTime,
        nullable=True,
        comment="Last message timestamp"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="conversations"
    )
    
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    
    current_assessment = relationship(
        "Assessment",
        foreign_keys=[current_assessment_id]
    )
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if conversation is active"""
        return self.status == ConversationStatus.ACTIVE
    
    def update_message_count(self):
        """Update message count"""
        self.message_count = len(self.messages) if self.messages else 0
    
    def update_last_message_time(self):
        """Update last message timestamp"""
        self.last_message_at = datetime.utcnow()
    
    def archive(self):
        """Archive conversation"""
        self.status = ConversationStatus.ARCHIVED
    
    def get_recent_messages(self, limit: int = 10):
        """Get recent messages"""
        if self.messages:
            return self.messages[-limit:]
        return []
    
    def to_safe_dict(self) -> dict:
        """Convert to dictionary with message summaries"""
        data = self.to_dict()
        if self.messages:
            data['message_summaries'] = [
                {
                    'id': msg.id,
                    'role': msg.role.value,
                    'content_preview': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
                    'created_at': msg.created_at.isoformat()
                }
                for msg in self.messages[-5:]  # Last 5 messages
            ]
        return data


class Message(BaseModel):
    """
    Message model for storing individual chat messages
    """
    __tablename__ = "messages"
    
    # Conversation relationship
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False,
        index=True,
        comment="Associated conversation ID"
    )
    
    # Message content
    role = Column(
        Enum(MessageRole),
        nullable=False,
        comment="Message role (user/assistant/system)"
    )
    
    content = Column(
        Text,
        nullable=False,
        comment="Message content"
    )
    
    # Message metadata
    token_count = Column(
        Integer,
        nullable=True,
        comment="Token count for the message"
    )
    
    processing_time_ms = Column(
        Integer,
        nullable=True,
        comment="Processing time in milliseconds"
    )
    
    # Model information
    model_used = Column(
        String(100),
        nullable=True,
        comment="AI model used for response"
    )
    
    # Message status
    is_edited = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether message has been edited"
    )
    
    edited_at = Column(
        DateTime,
        nullable=True,
        comment="Edit timestamp"
    )
    
    # Message feedback
    feedback_rating = Column(
        Integer,
        nullable=True,
        comment="User feedback rating (1-5)"
    )
    
    feedback_comment = Column(
        Text,
        nullable=True,
        comment="User feedback comment"
    )
    
    # Relationships
    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"
    
    @property
    def is_user_message(self) -> bool:
        """Check if message is from user"""
        return self.role == MessageRole.USER
    
    @property
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant"""
        return self.role == MessageRole.ASSISTANT
    
    @property
    def is_system_message(self) -> bool:
        """Check if message is from system"""
        return self.role == MessageRole.SYSTEM
    
    def edit(self, new_content: str):
        """Edit message content"""
        self.content = new_content
        self.is_edited = True
        self.edited_at = datetime.utcnow()
    
    def add_feedback(self, rating: int, comment: str = None):
        """Add user feedback to message"""
        self.feedback_rating = rating
        self.feedback_comment = comment
    
    def to_safe_dict(self) -> dict:
        """Convert to dictionary with content preview"""
        data = self.to_dict()
        data['content_preview'] = self.content[:200] + '...' if len(self.content) > 200 else self.content
        return data
