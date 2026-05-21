"""
Admin Router for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user, require_admin
from api.exceptions import NotFoundError, ValidationError

from models.user import User, UserRole, UserStatus
from datetime import datetime
from repositories.user_repository import UserRepository
from repositories.session_repository import SessionRepository
from repositories.assessment_repository import AssessmentRepository
from repositories.conversation_repository import ConversationRepository
from repositories.intervention_repository import InterventionRepository, UserInterventionRepository
from repositories.report_repository import ReportRepository

from schemas.user import UserListResponse, UserStatistics
from schemas.assessment import AssessmentStatistics
from schemas.conversation import ConversationStatistics
from schemas.intervention import InterventionStatistics
from schemas.common import SuccessResponse, PaginatedResponse, PaginationParams

from utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(session=db)


def get_session_repo(db: Session = Depends(get_db)) -> SessionRepository:
    return SessionRepository(session=db)


def get_assessment_repo(db: Session = Depends(get_db)) -> AssessmentRepository:
    return AssessmentRepository(session=db)


def get_conversation_repo(db: Session = Depends(get_db)) -> ConversationRepository:
    return ConversationRepository(session=db)


def get_intervention_repo(db: Session = Depends(get_db)) -> InterventionRepository:
    return InterventionRepository(session=db)


def get_user_intervention_repo(db: Session = Depends(get_db)) -> UserInterventionRepository:
    return UserInterventionRepository(session=db)


def get_report_repo(db: Session = Depends(get_db)) -> ReportRepository:
    return ReportRepository(session=db)


@router.get("/dashboard", response_model=dict)
async def admin_dashboard(
    current_user: User = Depends(require_admin),
    user_repo: UserRepository = Depends(get_user_repo),
    assessment_repo: AssessmentRepository = Depends(get_assessment_repo),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo),
    intervention_repo: InterventionRepository = Depends(get_intervention_repo),
    report_repo: ReportRepository = Depends(get_report_repo)
):
    """
    Admin dashboard with system overview statistics
    """
    logger.info(f"Admin dashboard accessed by user {current_user.id}")
    
    user_stats = user_repo.get_user_statistics(days=30)
    assessment_stats = assessment_repo.get_assessment_statistics(days=30)
    conversation_stats = conversation_repo.get_conversation_statistics()
    intervention_stats = intervention_repo.get_intervention_statistics()
    report_stats = report_repo.get_report_statistics(days=30)
    
    return {
        "users": user_stats,
        "assessments": assessment_stats,
        "conversations": conversation_stats,
        "interventions": intervention_stats,
        "reports": report_stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/users", response_model=PaginatedResponse)
async def list_all_users(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_admin),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    List all users with pagination (admin only)
    """
    users = user_repo.get_all(
        skip=(pagination.page - 1) * pagination.page_size,
        limit=pagination.page_size
    )
    
    total = user_repo.count()
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 1
    
    return PaginatedResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1,
        items=[UserListResponse.model_validate(u) for u in users]
    )


@router.delete("/users/{user_id}", response_model=SuccessResponse)
async def admin_delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Delete a user account (admin only)
    """
    if user_id == current_user.id:
        return SuccessResponse(
            success=False,
            message="Cannot delete your own admin account"
        )
    
    user = user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundError(resource="User", resource_id=str(user_id))
    
    success = user_repo.delete(user_id)
    
    if success:
        logger.info(f"Admin {current_user.id} deleted user {user_id}")
        return SuccessResponse(
            success=True,
            message="User deleted successfully"
        )
    else:
        return SuccessResponse(
            success=False,
            message="Failed to delete user"
        )


@router.post("/users/{user_id}/activate", response_model=SuccessResponse)
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Activate a user account (admin only)
    """
    user = user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundError(resource="User", resource_id=str(user_id))
    
    updated = user_repo.update_user_status(user_id, UserStatus.ACTIVE)
    
    if updated:
        logger.info(f"Admin {current_user.id} activated user {user_id}")
        return SuccessResponse(
            success=True,
            message="User activated successfully"
        )
    else:
        return SuccessResponse(
            success=False,
            message="Failed to activate user"
        )


@router.post("/users/{user_id}/suspend", response_model=SuccessResponse)
async def suspend_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """
    Suspend a user account (admin only)
    """
    if user_id == current_user.id:
        return SuccessResponse(
            success=False,
            message="Cannot suspend your own admin account"
        )
    
    user = user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundError(resource="User", resource_id=str(user_id))
    
    updated = user_repo.update_user_status(user_id, UserStatus.SUSPENDED)
    
    if updated:
        logger.info(f"Admin {current_user.id} suspended user {user_id}")
        return SuccessResponse(
            success=True,
            message="User suspended successfully"
        )
    else:
        return SuccessResponse(
            success=False,
            message="Failed to suspend user"
        )


@router.post("/maintenance/cleanup-sessions", response_model=SuccessResponse)
async def cleanup_expired_sessions(
    current_user: User = Depends(require_admin),
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """
    Clean up expired sessions (admin only)
    """
    cleaned = session_repo.cleanup_expired_sessions()
    
    logger.info(f"Admin {current_user.id} cleaned up {cleaned} expired sessions")
    
    return SuccessResponse(
        success=True,
        message=f"Cleaned up {cleaned} expired sessions",
        data={"cleaned_sessions": cleaned}
    )


@router.post("/maintenance/cleanup-reports", response_model=SuccessResponse)
async def cleanup_expired_reports(
    current_user: User = Depends(require_admin),
    report_repo: ReportRepository = Depends(get_report_repo)
):
    """
    Clean up expired reports (admin only)
    """
    cleaned = report_repo.cleanup_expired_reports()
    
    logger.info(f"Admin {current_user.id} cleaned up {cleaned} expired reports")
    
    return SuccessResponse(
        success=True,
        message=f"Cleaned up {cleaned} expired reports",
        data={"cleaned_reports": cleaned}
    )


@router.get("/system/health", response_model=dict)
async def system_health(
    current_user: User = Depends(require_admin)
):
    """
    System health check (admin only)
    """
    from db.connection import get_session_manager
    
    session_manager = get_session_manager()
    db_healthy = session_manager.check_connection()
    
    db_info = session_manager.get_database_info()
    
    return {
        "database": {
            "status": "healthy" if db_healthy else "unhealthy",
            "details": db_info
        },
        "api": {
            "status": "healthy",
            "version": "4.3.0"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
