"""
Conversation Schemas for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from models.conversation import ConversationStatus, MessageRole


class MessageBase(BaseModel):
    """Base message schema"""
    role: MessageRole = Field(description="Message role")
    content: str = Field(min_length=1, description="Message content")
    model_used: Optional[str] = Field(default=None, description="AI model used")


class MessageCreate(MessageBase):
    """Message creation schema"""
    conversation_id: int = Field(description="Conversation ID")
    token_count: Optional[int] = Field(default=None, description="Token count")


class MessageResponse(MessageBase):
    """Message response schema"""
    id: int = Field(description="Message ID")
    conversation_id: int = Field(description="Conversation ID")
    token_count: Optional[int] = Field(default=None, description="Token count")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time")
    is_edited: bool = Field(description="Whether message was edited")
    edited_at: Optional[datetime] = Field(default=None, description="Edit timestamp")
    feedback_rating: Optional[int] = Field(default=None, description="User feedback rating")
    feedback_comment: Optional[str] = Field(default=None, description="User feedback comment")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    
    model_config = ConfigDict(from_attributes=True)


class ConversationBase(BaseModel):
    """Base conversation schema"""
    title: Optional[str] = Field(default=None, max_length=255, description="Conversation title")
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE, description="Conversation status")
    context_data: Optional[Dict[str, Any]] = Field(default=None, description="Context data")


class ConversationCreate(ConversationBase):
    """Conversation creation schema"""
    user_id: int = Field(description="User ID")


class ConversationUpdate(BaseModel):
    """Conversation update schema"""
    title: Optional[str] = Field(default=None, max_length=255)
    status: Optional[ConversationStatus] = Field(default=None)
    context_data: Optional[Dict[str, Any]] = Field(default=None)
    current_assessment_id: Optional[int] = Field(default=None)


class ConversationResponse(ConversationBase):
    """Conversation response schema"""
    id: int = Field(description="Conversation ID")
    user_id: int = Field(description="User ID")
    message_count: int = Field(description="Message count")
    last_message_at: Optional[datetime] = Field(default=None, description="Last message time")
    messages: List[MessageResponse] = Field(default=[], description="Messages in conversation")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    
    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    """Conversation list response"""
    id: int
    user_id: int
    title: Optional[str]
    status: ConversationStatus
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MessageFeedbackRequest(BaseModel):
    """Message feedback request"""
    rating: int = Field(ge=1, le=5, description="Rating 1-5")
    comment: Optional[str] = Field(default=None, description="Optional comment")


class ConversationStatistics(BaseModel):
    """Conversation statistics"""
    total_conversations: int = Field(description="Total conversations")
    active_conversations: int = Field(description="Active conversations")
    archived_conversations: int = Field(description="Archived conversations")
    total_messages: int = Field(description="Total messages")
    avg_messages_per_conversation: float = Field(description="Average messages per conversation")
    period_days: int = Field(description="Statistics period")
