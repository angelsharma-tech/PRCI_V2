"""
Users Router for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user, require_admin, verify_user_access
from api.exceptions import NotFoundError, ValidationError

from models.user import User, UserStatus, UserRole
from repositories.user_repository import UserRepository

from schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserProfileResponse, UserStatusUpdate, UserRoleUpdate, UserStatistics
)
from schemas.common import SuccessResponse, PaginatedResponse, PaginationParams

from utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency to get user repository"""
    return UserRepository(session=db)


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Get current user's profile
    """
    # Get statistics
    stats = user_repo.get_user_statistics(days=30)
    
    user_dict = current_user.to_safe_dict()
    user_dict.update({
        "total_assessments": stats.get("total_assessments", 0),
        "total_conversations": stats.get("total_conversations", 0),
        "total_interventions": stats.get("total_interventions", 0),
        "total_reports": stats.get("total_reports", 0)
    })
    
    return UserProfileResponse(**user_dict)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    request: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Update current user's profile
    """
    logger.info(f"User {current_user.id} updating profile")
    
    update_data = request.model_dump(exclude_unset=True)
    
    updated_user = user_repo.update_user(current_user.id, **update_data)
    
    if not updated_user:
        raise ValidationError(message="Failed to update user profile")
    
    return UserResponse.model_validate(updated_user)


@router.delete("/me", response_model=SuccessResponse)
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Delete current user's account (soft delete)
    """
    logger.info(f"User {current_user.id} deleting account")
    
    success = user_repo.delete(current_user.id)
    
    if success:
        return SuccessResponse(
            success=True,
            message="Account deleted successfully"
        )
    else:
        return SuccessResponse(
            success=False,
            message="Failed to delete account"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Get user by ID (admin or self only)
    """
    verify_user_access(user_id, current_user)
    
    user = user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundError(resource="User", resource_id=str(user_id))
    
    return UserResponse.model_validate(user)


@router.get("", response_model=PaginatedResponse)
async def list_users(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_admin(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    List all users (admin only)
    """
    users = user_repo.get_all(
        skip=(pagination.page - 1) * pagination.page_size,
        limit=pagination.page_size
    )
    
    total = user_repo.count()
    
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1,
        items=[UserListResponse.model_validate(u) for u in users]
    )


@router.put("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    request: UserStatusUpdate,
    current_user: User = Depends(require_admin(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Update user status (admin only)
    """
    user = user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundError(resource="User", resource_id=str(user_id))
    
    updated_user = user_repo.update_user_status(user_id, request.status)
    
    if not updated_user:
        raise ValidationError(message="Failed to update user status")
    
    logger.info(f"User {user_id} status updated to {request.status.value} by admin {current_user.id}")
    
    return UserResponse.model_validate(updated_user)


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    request: UserRoleUpdate,
    current_user: User = Depends(require_admin(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Update user role (admin only)
    """
    user = user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundError(resource="User", resource_id=str(user_id))
    
    updated_user = user_repo.update_user_role(user_id, request.role)
    
    if not updated_user:
        raise ValidationError(message="Failed to update user role")
    
    logger.info(f"User {user_id} role updated to {request.role.value} by admin {current_user.id}")
    
    return UserResponse.model_validate(updated_user)


@router.get("/statistics/overview", response_model=UserStatistics)
async def get_user_statistics(
    current_user: User = Depends(require_admin(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Get user statistics (admin only)
    """
    stats = user_repo.get_user_statistics(days=30)
    
    return UserStatistics(
        total_users=stats.get("total_users", 0),
        active_users=stats.get("active_users", 0),
        new_users_today=stats.get("new_users_today", 0),
        new_users_week=stats.get("new_users_week", 0),
        new_users_month=stats.get("new_users_month", 0),
        users_by_status=stats.get("users_by_status", {}),
        users_by_role=stats.get("users_by_role", {})
    )
