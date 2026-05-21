"""
User Repository for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .base import BaseRepository
from models.user import User, UserStatus, UserRole
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class UserRepository(BaseRepository[User]):
    """
    Repository for User model operations
    """
    
    def get_model_class(self):
        return User
    
    # User-specific operations
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address"""
        try:
            return self.session.query(User).filter(
                and_(
                    User.email == email.lower(),
                    User.is_deleted == 'N'
                )
            ).first()
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}")
            raise
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        try:
            return self.session.query(User).filter(
                and_(
                    User.username == username,
                    User.is_deleted == 'N'
                )
            ).first()
        except Exception as e:
            logger.error(f"Error finding user by username {username}: {e}")
            raise
    
    def find_by_email_or_username(self, identifier: str) -> Optional[User]:
        """Find user by email or username"""
        try:
            return self.session.query(User).filter(
                and_(
                    or_(
                        User.email == identifier.lower(),
                        User.username == identifier
                    ),
                    User.is_deleted == 'N'
                )
            ).first()
        except Exception as e:
            logger.error(f"Error finding user by identifier {identifier}: {e}")
            raise
    
    def create_user(self, email: str, **kwargs) -> User:
        """
        Create a new user
        
        Args:
            email: User email address
            **kwargs: Additional user fields
            
        Returns:
            Created user instance
        """
        user_data = {
            'email': email.lower(),
            'status': UserStatus.ACTIVE,
            'role': UserRole.USER,
            **kwargs
        }
        
        # Set full name if first and last name provided
        if kwargs.get('first_name') and kwargs.get('last_name'):
            user_data['full_name'] = f"{kwargs['first_name']} {kwargs['last_name']}"
        
        return self.create(user_data)
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user information"""
        # Convert email to lowercase if provided
        if 'email' in kwargs:
            kwargs['email'] = kwargs['email'].lower()
        
        # Update full name if first or last name changed
        if 'first_name' in kwargs or 'last_name' in kwargs:
            user = self.get_by_id(user_id)
            if user:
                first_name = kwargs.get('first_name', user.first_name)
                last_name = kwargs.get('last_name', user.last_name)
                kwargs['full_name'] = f"{first_name} {last_name}" if first_name or last_name else None
        
        return self.update(user_id, kwargs)
    
    def get_active_users(self) -> List[User]:
        """Get all active users"""
        try:
            return self.session.query(User).filter(
                and_(
                    User.status == UserStatus.ACTIVE,
                    User.is_deleted == 'N'
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            raise
    
    def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        try:
            return self.session.query(User).filter(
                and_(
                    User.role == role,
                    User.is_deleted == 'N'
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting users by role {role}: {e}")
            raise
    
    def get_users_by_status(self, status: UserStatus) -> List[User]:
        """Get users by status"""
        try:
            return self.session.query(User).filter(
                and_(
                    User.status == status,
                    User.is_deleted == 'N'
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting users by status {status}: {e}")
            raise
    
    def search_users(self, search_term: str) -> List[User]:
        """Search users by name, email, or username"""
        search_fields = ['email', 'username', 'full_name', 'first_name', 'last_name']
        return self.search(search_term, search_fields)
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        try:
            user = self.get_by_id(user_id)
            if user:
                user.update_last_login()
                self.session.commit()
                logger.info(f"Updated last login for user {user_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating last login for user {user_id}: {e}")
            raise
    
    def verify_user_email(self, user_id: int) -> bool:
        """Mark user email as verified"""
        try:
            user = self.get_by_id(user_id)
            if user:
                user.verify_email()
                self.session.commit()
                logger.info(f"Verified email for user {user_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error verifying email for user {user_id}: {e}")
            raise
    
    def change_user_status(self, user_id: int, status: UserStatus) -> bool:
        """Change user status"""
        return self.update_user(user_id, status=status) is not None
    
    def change_user_role(self, user_id: int, role: UserRole) -> bool:
        """Change user role"""
        return self.update_user(user_id, role=role) is not None
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            total_users = self.session.query(User).filter(User.is_deleted == 'N').count()
            active_users = self.session.query(User).filter(
                and_(User.status == UserStatus.ACTIVE, User.is_deleted == 'N')
            ).count()
            verified_users = self.session.query(User).filter(
                and_(User.is_verified == True, User.is_deleted == 'N')
            ).count()
            
            # Recent registrations (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_users = self.session.query(User).filter(
                and_(
                    User.created_at >= thirty_days_ago,
                    User.is_deleted == 'N'
                )
            ).count()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'verified_users': verified_users,
                'recent_users': recent_users,
                'verification_rate': (verified_users / total_users * 100) if total_users > 0 else 0,
                'activity_rate': (active_users / total_users * 100) if total_users > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            raise
    
    def get_users_recently_active(self, days: int = 7) -> List[User]:
        """Get users who have been recently active"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return self.session.query(User).filter(
                and_(
                    User.last_login_at >= cutoff_date,
                    User.is_deleted == 'N'
                )
            ).order_by(User.last_login_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting recently active users: {e}")
            raise
    
    def check_email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        return self.exists(email=email.lower())
    
    def check_username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        return self.exists(username=username)
    
    def get_admin_users(self) -> List[User]:
        """Get all admin users"""
        return self.get_users_by_role(UserRole.ADMIN)
    
    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        import json
        return self.update_user(user_id, preferences=json.dumps(preferences)) is not None
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user preferences as dictionary"""
        user = self.get_by_id(user_id)
        if user and user.preferences:
            try:
                import json
                return json.loads(user.preferences)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def soft_delete_user(self, user_id: int) -> bool:
        """Soft delete user (deactivate and mark as deleted)"""
        try:
            user = self.get_by_id(user_id)
            if user:
                user.soft_delete()
                user.status = UserStatus.INACTIVE
                self.session.commit()
                logger.info(f"Soft deleted user {user_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error soft deleting user {user_id}: {e}")
            raise
