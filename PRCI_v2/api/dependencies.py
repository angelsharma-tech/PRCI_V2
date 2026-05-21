"""
API Dependencies for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from typing import Optional, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db.connection import get_session_manager
from repositories.user_repository import UserRepository
from models.user import User, UserRole

from auth.jwt_handler import verify_access_token
from auth.password_handler import verify_password

from utils.logging_utils import get_logger

logger = get_logger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


def get_db() -> Generator:
    """
    Dependency to get a database session
    """
    session_manager = get_session_manager()
    with session_manager.get_session() as session:
        yield session


def close_db_connections() -> None:
    """
    Close all database connections (used in lifespan shutdown)
    """
    try:
        session_manager = get_session_manager()
        session_manager.dispose()
        logger.info("All database connections disposed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    
    # Verify token
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get user from database
    try:
        user_repo = UserRepository(session=db)
        user = user_repo.get_by_id(int(user_id))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if user.is_deleted == 'Y':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user information"
        )


def require_role(required_role: UserRole):
    """
    Dependency factory to require a specific role
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    return role_checker


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require admin role
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_moderator_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require moderator or admin role
    """
    if current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator or admin access required"
        )
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally get the current user (returns None if not authenticated)
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_access_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user_repo = UserRepository(session=db)
        return user_repo.get_by_id(int(user_id))
        
    except Exception:
        return None


def verify_user_access(
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> bool:
    """
    Verify that the current user has access to the specified user_id's resources
    """
    if current_user.role == UserRole.ADMIN:
        return True
    
    if current_user.id == user_id:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied to this user's resources"
    )
