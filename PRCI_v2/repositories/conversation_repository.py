"""
Conversation Repository for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from .base import BaseRepository
from models.conversation import Conversation, Message, ConversationStatus, MessageRole
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation model operations
    """
    
    def get_model_class(self):
        return Conversation
    
    # Conversation-specific operations
    
    def create_conversation(self, user_id: int, title: str = None, 
                         status: ConversationStatus = ConversationStatus.ACTIVE) -> Conversation:
        """Create a new conversation"""
        conversation_data = {
            'user_id': user_id,
            'title': title or f"Conversation - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            'status': status
        }
        
        return self.create(conversation_data)
    
    def get_user_conversations(self, user_id: int, include_deleted: bool = False) -> List[Conversation]:
        """Get all conversations for a user"""
        try:
            query = self.session.query(Conversation).filter(Conversation.user_id == user_id)
            
            if not include_deleted:
                query = query.filter(Conversation.is_deleted == 'N')
            
            return query.order_by(desc(Conversation.last_message_at)).all()
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {e}")
            raise
    
    def get_active_conversations(self, user_id: int) -> List[Conversation]:
        """Get active conversations for a user"""
        try:
            return self.session.query(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.status == ConversationStatus.ACTIVE,
                    Conversation.is_deleted == 'N'
                )
            ).order_by(desc(Conversation.last_message_at)).all()
        except Exception as e:
            logger.error(f"Error getting active conversations: {e}")
            raise
    
    def get_archived_conversations(self, user_id: int) -> List[Conversation]:
        """Get archived conversations for a user"""
        try:
            return self.session.query(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.status == ConversationStatus.ARCHIVED,
                    Conversation.is_deleted == 'N'
                )
            ).order_by(desc(Conversation.last_message_at)).all()
        except Exception as e:
            logger.error(f"Error getting archived conversations: {e}")
            raise
    
    def archive_conversation(self, conversation_id: int) -> bool:
        """Archive a conversation"""
        try:
            conversation = self.get_by_id(conversation_id)
            if conversation:
                conversation.archive()
                self.session.commit()
                logger.info(f"Archived conversation {conversation_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error archiving conversation {conversation_id}: {e}")
            raise
    
    def update_conversation_activity(self, conversation_id: int) -> bool:
        """Update conversation activity timestamp and message count"""
        try:
            conversation = self.get_by_id(conversation_id)
            if conversation:
                conversation.update_last_message_time()
                conversation.update_message_count()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating conversation activity {conversation_id}: {e}")
            raise
    
    def get_conversation_statistics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get conversation statistics for a user"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = self.session.query(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.created_at >= cutoff_date,
                    Conversation.is_deleted == 'N'
                )
            )
            
            total_conversations = query.count()
            active_conversations = query.filter(
                Conversation.status == ConversationStatus.ACTIVE
            ).count()
            archived_conversations = query.filter(
                Conversation.status == ConversationStatus.ARCHIVED
            ).count()
            
            # Total messages
            total_messages = self.session.query(func.count(Message.id)).join(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.created_at >= cutoff_date,
                    Conversation.is_deleted == 'N',
                    Message.is_deleted == 'N'
                )
            ).scalar() or 0
            
            # Average messages per conversation
            avg_messages = total_messages / total_conversations if total_conversations > 0 else 0
            
            return {
                'total_conversations': total_conversations,
                'active_conversations': active_conversations,
                'archived_conversations': archived_conversations,
                'total_messages': total_messages,
                'avg_messages_per_conversation': avg_messages,
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting conversation statistics: {e}")
            raise
    
    def search_conversations(self, user_id: int, search_term: str) -> List[Conversation]:
        """Search conversations by title or content"""
        # Search in conversation titles and message content
        try:
            conversations = self.session.query(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.is_deleted == 'N'
                )
            ).filter(
                Conversation.title.contains(search_term)
            ).all()
            
            # Also search in message content
            message_conversations = self.session.query(Conversation).join(Message).filter(
                and_(
                    Conversation.user_id == user_id,
                    Message.content.contains(search_term),
                    Conversation.is_deleted == 'N',
                    Message.is_deleted == 'N'
                )
            ).distinct().all()
            
            # Combine and remove duplicates
            all_conversations = list(set(conversations + message_conversations))
            
            return sorted(all_conversations, key=lambda x: x.last_message_at or x.created_at, reverse=True)
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            raise


class MessageRepository(BaseRepository[Message]):
    """
    Repository for Message model operations
    """
    
    def get_model_class(self):
        return Message
    
    # Message-specific operations
    
    def create_message(self, conversation_id: int, role: MessageRole, 
                    content: str, **kwargs) -> Message:
        """Create a new message"""
        message_data = {
            'conversation_id': conversation_id,
            'role': role,
            'content': content,
            **kwargs
        }
        
        message = self.create(message_data)
        
        # Update conversation activity
        conv_repo = ConversationRepository(self.session)
        conv_repo.update_conversation_activity(conversation_id)
        
        return message
    
    def get_conversation_messages(self, conversation_id: int, 
                             limit: int = None, include_deleted: bool = False) -> List[Message]:
        """Get messages for a conversation"""
        try:
            query = self.session.query(Message).filter(Message.conversation_id == conversation_id)
            
            if not include_deleted:
                query = query.filter(Message.is_deleted == 'N')
            
            query = query.order_by(Message.created_at)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
            raise
    
    def get_recent_messages(self, conversation_id: int, count: int = 10) -> List[Message]:
        """Get recent messages for a conversation"""
        messages = self.get_conversation_messages(conversation_id)
        return messages[-count:] if messages else []
    
    def get_user_messages(self, user_id: int, role: MessageRole = None, 
                       days: int = 30) -> List[Message]:
        """Get messages for a user by role"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = self.session.query(Message).join(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Message.created_at >= cutoff_date,
                    Conversation.is_deleted == 'N',
                    Message.is_deleted == 'N'
                )
            )
            
            if role:
                query = query.filter(Message.role == role)
            
            return query.order_by(desc(Message.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting user messages: {e}")
            raise
    
    def add_feedback(self, message_id: int, rating: int, comment: str = None) -> bool:
        """Add feedback to a message"""
        try:
            message = self.get_by_id(message_id)
            if message:
                message.add_feedback(rating, comment)
                self.session.commit()
                logger.info(f"Added feedback to message {message_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding feedback to message {message_id}: {e}")
            raise
    
    def edit_message(self, message_id: int, new_content: str) -> bool:
        """Edit a message"""
        try:
            message = self.get_by_id(message_id)
            if message:
                message.edit(new_content)
                self.session.commit()
                logger.info(f"Edited message {message_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error editing message {message_id}: {e}")
            raise
    
    def get_message_statistics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get message statistics for a user"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Total messages by role
            message_counts = self.session.query(
                Message.role,
                func.count(Message.id).label('count')
            ).join(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Message.created_at >= cutoff_date,
                    Conversation.is_deleted == 'N',
                    Message.is_deleted == 'N'
                )
            ).group_by(Message.role).all()
            
            # Average processing time for assistant messages
            avg_processing_time = self.session.query(
                func.avg(Message.processing_time_ms)
            ).join(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Message.role == MessageRole.ASSISTANT,
                    Message.processing_time_ms.isnot(None),
                    Message.created_at >= cutoff_date,
                    Conversation.is_deleted == 'N',
                    Message.is_deleted == 'N'
                )
            ).scalar() or 0
            
            # Feedback statistics
            feedback_stats = self.session.query(
                func.avg(Message.feedback_rating).label('avg_rating'),
                func.count(Message.feedback_rating).label('feedback_count')
            ).join(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Message.feedback_rating.isnot(None),
                    Message.created_at >= cutoff_date,
                    Conversation.is_deleted == 'N',
                    Message.is_deleted == 'N'
                )
            ).first()
            
            return {
                'message_counts': dict(message_counts),
                'total_messages': sum(count for role, count in message_counts),
                'avg_processing_time_ms': avg_processing_time,
                'feedback_stats': {
                    'average_rating': feedback_stats.avg_rating if feedback_stats else 0,
                    'feedback_count': feedback_stats.feedback_count if feedback_stats else 0
                },
                'period_days': days
            }
        except Exception as e:
            logger.error(f"Error getting message statistics: {e}")
            raise
    
    def search_messages(self, user_id: int, search_term: str) -> List[Message]:
        """Search messages by content"""
        try:
            return self.session.query(Message).join(Conversation).filter(
                and_(
                    Conversation.user_id == user_id,
                    Message.content.contains(search_term),
                    Conversation.is_deleted == 'N',
                    Message.is_deleted == 'N'
                )
            ).order_by(desc(Message.created_at)).all()
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            raise
    
    def get_conversation_context(self, conversation_id: int, message_count: int = 10) -> List[Dict[str, Any]]:
        """Get conversation context for AI processing"""
        messages = self.get_conversation_messages(conversation_id, limit=message_count)
        
        return [
            {
                'role': message.role.value,
                'content': message.content,
                'timestamp': message.created_at.isoformat(),
                'id': message.id
            }
            for message in messages
        ]
