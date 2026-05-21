"""
Auth Service for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from models.user import User, UserStatus, UserRole
from repositories.user_repository import UserRepository

from .jwt_handler import create_access_token, create_refresh_token, verify_refresh_token
from .password_handler import hash_password, verify_password, generate_password_reset_token, verify_password_reset_token

from utils.logging_utils import get_logger
from api.exceptions import AuthenticationError, ValidationError, ConflictError, NotFoundError

logger = get_logger(__name__)


class AuthService:
    """
    Authentication service handling user authentication flows
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(session=db)
    
    def register(self, email: str, password: str, first_name: str, 
                last_name: str = None, username: str = None, **kwargs) -> Dict[str, Any]:
        """
        Register a new user
        """
        try:
            # Check if user already exists
            existing_user = self.user_repo.find_by_email(email)
            if existing_user:
                logger.warning(f"Registration attempt with existing email: {email}")
                raise ConflictError(
                    message="Email already registered",
                    details={"email": email}
                )
            
            # Check username if provided
            if username:
                existing_username = self.user_repo.find_by_username(username)
                if existing_username:
                    logger.warning(f"Registration attempt with existing username: {username}")
                    raise ConflictError(
                        message="Username already taken",
                        details={"username": username}
                    )
            
            # Hash password
            password_hash = hash_password(password)
            
            # Create user
            user = self.user_repo.create_user(
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                username=username,
                status=UserStatus.ACTIVE,  # Auto-activate for now (email verification can be added later)
                role=UserRole.USER,
                **kwargs
            )
            
            if not user:
                logger.error("Failed to create user during registration")
                raise AuthenticationError(message="Failed to create user account")
            
            # Generate tokens
            access_token = create_access_token(
                user_id=user.id,
                email=user.email,
                role=user.role.value
            )
            refresh_token = create_refresh_token(user_id=user.id)
            
            logger.info(f"User registered successfully: {email}")
            
            return {
                "user": user.to_safe_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except ConflictError:
            raise
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise AuthenticationError(message="Registration failed")
    
    def login(self, email: str, password: str, remember_me: bool = False) -> Dict[str, Any]:
        """
        Authenticate user and generate tokens
        """
        try:
            # Find user by email
            user = self.user_repo.find_by_email(email)
            
            if not user:
                logger.warning(f"Login attempt for non-existent email: {email}")
                raise AuthenticationError(message="Invalid email or password")
            
            # Check user status
            if user.status != UserStatus.ACTIVE:
                logger.warning(f"Login attempt for inactive user: {email}")
                raise AuthenticationError(
                    message="Account is not active",
                    details={"status": user.status.value}
                )
            
            if user.is_deleted == 'Y':
                logger.warning(f"Login attempt for deleted user: {email}")
                raise AuthenticationError(message="Account has been deactivated")
            
            # Verify password
            if not user.password_hash or not verify_password(password, user.password_hash):
                logger.warning(f"Failed login attempt for user: {email}")
                raise AuthenticationError(message="Invalid email or password")
            
            # Update last login
            self.user_repo.update_last_login(user.id)
            
            # Generate tokens
            access_token = create_access_token(
                user_id=user.id,
                email=user.email,
                role=user.role.value
            )
            refresh_token = create_refresh_token(user_id=user.id)
            
            logger.info(f"User logged in successfully: {email}")
            
            return {
                "user": user.to_safe_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise AuthenticationError(message="Login failed")
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        """
        try:
            # Verify refresh token
            payload = verify_refresh_token(refresh_token)
            if not payload:
                logger.warning("Invalid or expired refresh token")
                raise AuthenticationError(message="Invalid or expired refresh token")
            
            user_id = int(payload.get("sub"))
            
            # Get user
            user = self.user_repo.get_by_id(user_id)
            if not user:
                logger.warning(f"User not found for refresh token: {user_id}")
                raise AuthenticationError(message="User not found")
            
            # Check user status
            if user.status != UserStatus.ACTIVE or user.is_deleted == 'Y':
                logger.warning(f"Inactive user attempted token refresh: {user_id}")
                raise AuthenticationError(message="Account is not active")
            
            # Generate new tokens
            new_access_token = create_access_token(
                user_id=user.id,
                email=user.email,
                role=user.role.value
            )
            new_refresh_token = create_refresh_token(user_id=user.id)
            
            logger.info(f"Token refreshed for user: {user.email}")
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise AuthenticationError(message="Token refresh failed")
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change user password
        """
        try:
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise NotFoundError(resource="User", resource_id=str(user_id))
            
            # Verify current password
            if not user.password_hash or not verify_password(current_password, user.password_hash):
                logger.warning(f"Password change failed - incorrect current password: {user_id}")
                raise AuthenticationError(message="Current password is incorrect")
            
            # Hash new password
            new_password_hash = hash_password(new_password)
            
            # Update password
            updated_user = self.user_repo.update_password(user_id, new_password_hash)
            
            if updated_user:
                logger.info(f"Password changed successfully for user: {user_id}")
                return True
            else:
                logger.error(f"Failed to update password for user: {user_id}")
                return False
                
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Password change error: {e}")
            raise AuthenticationError(message="Password change failed")
    
    def request_password_reset(self, email: str) -> bool:
        """
        Request password reset
        """
        try:
            user = self.user_repo.find_by_email(email)
            if not user:
                # Don't reveal if email exists
                logger.info(f"Password reset requested for non-existent email: {email}")
                return True  # Still return True to prevent email enumeration
            
            # Generate reset token
            token = generate_password_reset_token(user.id)
            
            # In production, send email with reset link
            # For now, just log the token
            logger.info(f"Password reset token generated for user: {email} (token: {token})")
            
            return True
            
        except Exception as e:
            logger.error(f"Password reset request error: {e}")
            # Don't raise error to prevent email enumeration
            return True
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password using reset token
        """
        try:
            # Verify token
            user_id = verify_password_reset_token(token)
            if not user_id:
                logger.warning("Invalid or expired password reset token")
                raise AuthenticationError(message="Invalid or expired reset token")
            
            # Get user
            user = self.user_repo.get_by_id(user_id)
            if not user:
                logger.warning(f"User not found for password reset: {user_id}")
                raise AuthenticationError(message="User not found")
            
            # Hash new password
            new_password_hash = hash_password(new_password)
            
            # Update password
            updated_user = self.user_repo.update_password(user_id, new_password_hash)
            
            if updated_user:
                logger.info(f"Password reset successfully for user: {user_id}")
                # Mark token as used
                from .password_handler import mark_password_reset_token_used
                mark_password_reset_token_used(token)
                return True
            else:
                logger.error(f"Failed to reset password for user: {user_id}")
                return False
                
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            raise AuthenticationError(message="Password reset failed")
    
    def logout(self, user_id: int, all_devices: bool = False) -> bool:
        """
        Logout user
        """
        try:
            # In a production app, you would:
            # 1. Add token to a blacklist (Redis/database)
            # 2. If all_devices, invalidate all user tokens
            # 3. Deactivate user sessions
            
            logger.info(f"User logged out: {user_id} (all_devices: {all_devices})")
            return True
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False


# Global auth service instance
_auth_service_instance = None


def get_auth_service(db: Session) -> AuthService:
    """
    Get auth service instance
    """
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService(db)
    return _auth_service_instance
