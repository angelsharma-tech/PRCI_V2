"""
Interventions Router for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user, verify_user_access, require_role
from api.exceptions import NotFoundError, ValidationError

from models.user import User
from models.intervention import Intervention, UserIntervention, InterventionStatus, UserInterventionStatus
from repositories.intervention_repository import InterventionRepository, UserInterventionRepository

from schemas.intervention import (
    InterventionCreate, InterventionUpdate, InterventionResponse,
    InterventionListResponse, UserInterventionCreate, UserInterventionUpdate,
    UserInterventionResponse, InterventionStatistics
)
from schemas.common import SuccessResponse, PaginatedResponse, PaginationParams

from utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_intervention_repo(db: Session = Depends(get_db)) -> InterventionRepository:
    """Dependency to get intervention repository"""
    return InterventionRepository(session=db)


def get_user_intervention_repo(db: Session = Depends(get_db)) -> UserInterventionRepository:
    """Dependency to get user intervention repository"""
    return UserInterventionRepository(session=db)


# --- Intervention Template Routes (Admin/Managed) ---

@router.get("/templates", response_model=PaginatedResponse)
async def list_intervention_templates(
    pagination: PaginationParams = Depends(),
    intervention_type: str = None,
    category: str = None,
    current_user: User = Depends(get_current_user),
    intervention_repo: InterventionRepository = Depends(get_intervention_repo)
):
    """
    List intervention templates
    """
    interventions = intervention_repo.get_active_interventions(
        limit=pagination.page_size
    )
    
    # Filter by type/category if provided
    if intervention_type or category:
        filtered = []
        for intervention in interventions:
            if intervention_type and intervention.intervention_type.value != intervention_type:
                continue
            if category and intervention.category.value != category:
                continue
            filtered.append(intervention)
        interventions = filtered
    
    all_interventions = intervention_repo.get_active_interventions()
    total = len(all_interventions)
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 1
    
    return PaginatedResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1,
        items=[InterventionListResponse.model_validate(i) for i in interventions]
    )


@router.get("/templates/{intervention_id}", response_model=InterventionResponse)
async def get_intervention_template(
    intervention_id: int,
    current_user: User = Depends(get_current_user),
    intervention_repo: InterventionRepository = Depends(get_intervention_repo)
):
    """
    Get intervention template by ID
    """
    intervention = intervention_repo.get_by_id(intervention_id)
    if not intervention:
        raise NotFoundError(resource="Intervention", resource_id=str(intervention_id))
    
    return InterventionResponse.model_validate(intervention)


@router.post("/templates", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED)
async def create_intervention_template(
    request: InterventionCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    intervention_repo: InterventionRepository = Depends(get_intervention_repo)
):
    """
    Create intervention template (admin only)
    """
    intervention = intervention_repo.create_intervention(
        title=request.title,
        description=request.description,
        intervention_type=request.intervention_type,
        category=request.category,
        duration_minutes=request.duration_minutes,
        difficulty_level=request.difficulty_level,
        priority=request.priority,
        instructions=request.instructions,
        resources=request.resources,
        evidence_based=request.evidence_based,
        target_root_causes=request.target_root_causes,
        target_risk_levels=request.target_risk_levels,
        target_score_ranges=request.target_score_ranges,
        version=request.version
    )
    
    if not intervention:
        raise ValidationError(message="Failed to create intervention template")
    
    logger.info(f"Intervention template created by admin {current_user.id}")
    
    return InterventionResponse.model_validate(intervention)


@router.put("/templates/{intervention_id}", response_model=InterventionResponse)
async def update_intervention_template(
    intervention_id: int,
    request: InterventionUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    intervention_repo: InterventionRepository = Depends(get_intervention_repo)
):
    """
    Update intervention template (admin only)
    """
    intervention = intervention_repo.get_by_id(intervention_id)
    if not intervention:
        raise NotFoundError(resource="Intervention", resource_id=str(intervention_id))
    
    update_data = request.model_dump(exclude_unset=True)
    updated = intervention_repo.update(intervention_id, **update_data)
    
    if not updated:
        raise ValidationError(message="Failed to update intervention template")
    
    logger.info(f"Intervention template {intervention_id} updated by admin {current_user.id}")
    
    return InterventionResponse.model_validate(updated)


# --- User Intervention Routes ---

@router.get("/user", response_model=PaginatedResponse)
async def list_user_interventions(
    user_id: int,
    pagination: PaginationParams = Depends(),
    status_filter: UserInterventionStatus = None,
    current_user: User = Depends(get_current_user),
    user_intervention_repo: UserInterventionRepository = Depends(get_user_intervention_repo)
):
    """
    List interventions for a user
    """
    verify_user_access(user_id, current_user)
    
    interventions = user_intervention_repo.get_user_interventions(
        user_id=user_id,
        status=status_filter,
        limit=pagination.page_size
    )
    
    all_interventions = user_intervention_repo.get_user_interventions(
        user_id=user_id,
        status=status_filter
    )
    total = len(all_interventions)
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 1
    
    return PaginatedResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1,
        items=[UserInterventionResponse.model_validate(ui) for ui in interventions]
    )


@router.get("/user/{user_intervention_id}", response_model=UserInterventionResponse)
async def get_user_intervention(
    user_intervention_id: int,
    current_user: User = Depends(get_current_user),
    user_intervention_repo: UserInterventionRepository = Depends(get_user_intervention_repo)
):
    """
    Get user intervention by ID
    """
    user_intervention = user_intervention_repo.get_by_id(user_intervention_id)
    if not user_intervention:
        raise NotFoundError(resource="User Intervention", resource_id=str(user_intervention_id))
    
    verify_user_access(user_intervention.user_id, current_user)
    
    return UserInterventionResponse.model_validate(user_intervention)


@router.post("/recommend", response_model=UserInterventionResponse, status_code=status.HTTP_201_CREATED)
async def recommend_intervention(
    request: UserInterventionCreate,
    current_user: User = Depends(get_current_user),
    user_intervention_repo: UserInterventionRepository = Depends(get_user_intervention_repo)
):
    """
    Recommend an intervention to a user
    """
    verify_user_access(request.user_id, current_user)
    
    user_intervention = user_intervention_repo.recommend_intervention(
        user_id=request.user_id,
        intervention_id=request.intervention_id,
        assessment_id=request.assessment_id,
        personalized_notes=request.personalized_notes
    )
    
    if not user_intervention:
        raise ValidationError(message="Failed to recommend intervention")
    
    return UserInterventionResponse.model_validate(user_intervention)


@router.put("/user/{user_intervention_id}/accept", response_model=UserInterventionResponse)
async def accept_intervention(
    user_intervention_id: int,
    current_user: User = Depends(get_current_user),
    user_intervention_repo: UserInterventionRepository = Depends(get_user_intervention_repo)
):
    """
    Accept a recommended intervention
    """
    user_intervention = user_intervention_repo.get_by_id(user_intervention_id)
    if not user_intervention:
        raise NotFoundError(resource="User Intervention", resource_id=str(user_intervention_id))
    
    verify_user_access(user_intervention.user_id, current_user)
    
    success = user_intervention_repo.accept_intervention(user_intervention_id)
    if not success:
        raise ValidationError(message="Failed to accept intervention")
    
    updated = user_intervention_repo.get_by_id(user_intervention_id)
    return UserInterventionResponse.model_validate(updated)


@router.put("/user/{user_intervention_id}", response_model=UserInterventionResponse)
async def update_user_intervention(
    user_intervention_id: int,
    request: UserInterventionUpdate,
    current_user: User = Depends(get_current_user),
    user_intervention_repo: UserInterventionRepository = Depends(get_user_intervention_repo)
):
    """
    Update user intervention progress
    """
    user_intervention = user_intervention_repo.get_by_id(user_intervention_id)
    if not user_intervention:
        raise NotFoundError(resource="User Intervention", resource_id=str(user_intervention_id))
    
    verify_user_access(user_intervention.user_id, current_user)
    
    update_data = request.model_dump(exclude_unset=True)
    updated = user_intervention_repo.update(user_intervention_id, **update_data)
    
    if not updated:
        raise ValidationError(message="Failed to update user intervention")
    
    return UserInterventionResponse.model_validate(updated)


@router.put("/user/{user_intervention_id}/complete", response_model=UserInterventionResponse)
async def complete_intervention(
    user_intervention_id: int,
    request: UserInterventionUpdate,
    current_user: User = Depends(get_current_user),
    user_intervention_repo: UserInterventionRepository = Depends(get_user_intervention_repo)
):
    """
    Complete an intervention
    """
    user_intervention = user_intervention_repo.get_by_id(user_intervention_id)
    if not user_intervention:
        raise NotFoundError(resource="User Intervention", resource_id=str(user_intervention_id))
    
    verify_user_access(user_intervention.user_id, current_user)
    
    success = user_intervention_repo.complete_intervention(
        user_intervention_id=user_intervention_id,
        rating=request.user_rating,
        feedback=request.user_feedback,
        effectiveness=request.effectiveness_rating
    )
    
    if not success:
        raise ValidationError(message="Failed to complete intervention")
    
    updated = user_intervention_repo.get_by_id(user_intervention_id)
    return UserInterventionResponse.model_validate(updated)


@router.delete("/user/{user_intervention_id}", response_model=SuccessResponse)
async def delete_user_intervention(
    user_intervention_id: int,
    current_user: User = Depends(get_current_user),
    user_intervention_repo: UserInterventionRepository = Depends(get_user_intervention_repo)
):
    """
    Delete a user intervention
    """
    user_intervention = user_intervention_repo.get_by_id(user_intervention_id)
    if not user_intervention:
        raise NotFoundError(resource="User Intervention", resource_id=str(user_intervention_id))
    
    verify_user_access(user_intervention.user_id, current_user)
    
    success = user_intervention_repo.delete(user_intervention_id)
    
    if success:
        return SuccessResponse(
            success=True,
            message="User intervention deleted successfully"
        )
    else:
        return SuccessResponse(
            success=False,
            message="Failed to delete user intervention"
        )


@router.get("/statistics/overview", response_model=InterventionStatistics)
async def get_intervention_statistics(
    current_user: User = Depends(get_current_user),
    intervention_repo: InterventionRepository = Depends(get_intervention_repo),
    user_intervention_repo: UserInterventionRepository = Depends(get_user_intervention_repo)
):
    """
    Get intervention statistics
    """
    template_stats = intervention_repo.get_intervention_statistics()
    user_stats = user_intervention_repo.get_recommendation_statistics()
    
    return InterventionStatistics(
        total_interventions=template_stats.get("total_interventions", 0),
        active_interventions=template_stats.get("active_interventions", 0),
        total_recommendations=user_stats.get("total_recommendations", 0),
        completion_rate=template_stats.get("avg_completion_rate", 0.0),
        avg_effectiveness=template_stats.get("avg_effectiveness", 0.0),
        avg_user_rating=template_stats.get("avg_user_rating", 0.0)
    )
