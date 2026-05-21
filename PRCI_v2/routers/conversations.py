"""
Conversations Router for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user, verify_user_access
from api.exceptions import NotFoundError, ValidationError

from models.user import User
from models.conversation import Conversation, Message, ConversationStatus, MessageRole
from repositories.conversation_repository import ConversationRepository, MessageRepository

from schemas.conversation import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationListResponse, MessageCreate, MessageResponse,
    MessageFeedbackRequest, ConversationStatistics
)
from schemas.common import SuccessResponse, PaginatedResponse, PaginationParams

from utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_conversation_repo(db: Session = Depends(get_db)) -> ConversationRepository:
    """Dependency to get conversation repository"""
    return ConversationRepository(session=db)


def get_message_repo(db: Session = Depends(get_db)) -> MessageRepository:
    """Dependency to get message repository"""
    return MessageRepository(session=db)


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo)
):
    """
    Create a new conversation
    """
    verify_user_access(request.user_id, current_user)
    
    conversation = conversation_repo.create_conversation(
        user_id=request.user_id,
        title=request.title,
        status=request.status,
        context_data=request.context_data
    )
    
    if not conversation:
        raise ValidationError(message="Failed to create conversation")
    
    return ConversationResponse.model_validate(conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo),
    message_repo: MessageRepository = Depends(get_message_repo)
):
    """
    Get conversation by ID with messages
    """
    conversation = conversation_repo.get_by_id(conversation_id)
    if not conversation:
        raise NotFoundError(resource="Conversation", resource_id=str(conversation_id))
    
    verify_user_access(conversation.user_id, current_user)
    
    # Get messages
    messages = message_repo.get_conversation_messages(conversation_id)
    
    conversation_dict = conversation.to_safe_dict()
    conversation_dict["messages"] = [MessageResponse.model_validate(m) for m in messages]
    
    return ConversationResponse(**conversation_dict)


@router.get("", response_model=PaginatedResponse)
async def list_user_conversations(
    user_id: int,
    pagination: PaginationParams = Depends(),
    status_filter: ConversationStatus = None,
    current_user: User = Depends(get_current_user),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo)
):
    """
    List conversations for a user
    """
    verify_user_access(user_id, current_user)
    
    conversations = conversation_repo.get_user_conversations(
        user_id=user_id,
        limit=pagination.page_size,
        status=status_filter
    )
    
    all_conversations = conversation_repo.get_user_conversations(
        user_id=user_id,
        status=status_filter
    )
    total = len(all_conversations)
    
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 1
    
    return PaginatedResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1,
        items=[ConversationListResponse.model_validate(c) for c in conversations]
    )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    request: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo)
):
    """
    Update a conversation
    """
    conversation = conversation_repo.get_by_id(conversation_id)
    if not conversation:
        raise NotFoundError(resource="Conversation", resource_id=str(conversation_id))
    
    verify_user_access(conversation.user_id, current_user)
    
    update_data = request.model_dump(exclude_unset=True)
    updated = conversation_repo.update(conversation_id, **update_data)
    
    if not updated:
        raise ValidationError(message="Failed to update conversation")
    
    return ConversationResponse.model_validate(updated)


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: int,
    request: MessageCreate,
    current_user: User = Depends(get_current_user),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo),
    message_repo: MessageRepository = Depends(get_message_repo)
):
    """
    Add a message to a conversation
    """
    conversation = conversation_repo.get_by_id(conversation_id)
    if not conversation:
        raise NotFoundError(resource="Conversation", resource_id=str(conversation_id))
    
    verify_user_access(conversation.user_id, current_user)
    
    message = message_repo.create_message(
        conversation_id=conversation_id,
        role=request.role,
        content=request.content,
        token_count=request.token_count,
        model_used=request.model_used
    )
    
    if not message:
        raise ValidationError(message="Failed to create message")
    
    return MessageResponse.model_validate(message)


@router.put("/{conversation_id}/messages/{message_id}/feedback", response_model=MessageResponse)
async def add_message_feedback(
    conversation_id: int,
    message_id: int,
    request: MessageFeedbackRequest,
    current_user: User = Depends(get_current_user),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo),
    message_repo: MessageRepository = Depends(get_message_repo)
):
    """
    Add feedback to a message
    """
    conversation = conversation_repo.get_by_id(conversation_id)
    if not conversation:
        raise NotFoundError(resource="Conversation", resource_id=str(conversation_id))
    
    verify_user_access(conversation.user_id, current_user)
    
    updated = message_repo.add_feedback(message_id, request.rating, request.comment)
    
    if not updated:
        raise ValidationError(message="Failed to add feedback")
    
    message = message_repo.get_by_id(message_id)
    return MessageResponse.model_validate(message)


@router.delete("/{conversation_id}", response_model=SuccessResponse)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo)
):
    """
    Delete a conversation (soft delete)
    """
    conversation = conversation_repo.get_by_id(conversation_id)
    if not conversation:
        raise NotFoundError(resource="Conversation", resource_id=str(conversation_id))
    
    verify_user_access(conversation.user_id, current_user)
    
    success = conversation_repo.delete(conversation_id)
    
    if success:
        return SuccessResponse(
            success=True,
            message="Conversation deleted successfully"
        )
    else:
        return SuccessResponse(
            success=False,
            message="Failed to delete conversation"
        )


@router.get("/statistics/overview", response_model=ConversationStatistics)
async def get_conversation_statistics(
    current_user: User = Depends(get_current_user),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo)
):
    """
    Get conversation statistics
    """
    stats = conversation_repo.get_conversation_statistics()
    
    return ConversationStatistics(
        total_conversations=stats.get("total_conversations", 0),
        active_conversations=stats.get("active_conversations", 0),
        archived_conversations=stats.get("archived_conversations", 0),
        total_messages=stats.get("total_messages", 0),
        avg_messages_per_conversation=stats.get("avg_messages_per_conversation", 0.0),
        period_days=stats.get("period_days", 30)
    )
