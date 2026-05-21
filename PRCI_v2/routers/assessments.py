"""
Assessments Router for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user, verify_user_access
from api.exceptions import NotFoundError, ValidationError

from models.user import User
from models.assessment import Assessment, AssessmentType, AssessmentStatus, ScoreType
from repositories.assessment_repository import AssessmentRepository, ScoreRepository

from schemas.assessment import (
    AssessmentCreate, AssessmentUpdate, AssessmentResponse,
    AssessmentListResponse, AssessmentCompleteRequest, AssessmentStatistics,
    ScoreCreate, ScoreResponse
)
from schemas.common import SuccessResponse, PaginatedResponse, PaginationParams

from utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_assessment_repo(db: Session = Depends(get_db)) -> AssessmentRepository:
    """Dependency to get assessment repository"""
    return AssessmentRepository(session=db)


def get_score_repo(db: Session = Depends(get_db)) -> ScoreRepository:
    """Dependency to get score repository"""
    return ScoreRepository(session=db)


@router.post("", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    request: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    assessment_repo: AssessmentRepository = Depends(get_assessment_repo)
):
    """
    Create a new assessment
    """
    logger.info(f"Creating assessment for user {request.user_id}")
    
    verify_user_access(request.user_id, current_user)
    
    assessment = assessment_repo.create_assessment(
        user_id=request.user_id,
        assessment_type=request.assessment_type,
        title=request.title,
        description=request.description,
        input_text=request.input_text,
        input_data=request.input_data,
        model_version=request.model_version
    )
    
    if not assessment:
        raise ValidationError(message="Failed to create assessment")
    
    return AssessmentResponse.model_validate(assessment)


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    assessment_repo: AssessmentRepository = Depends(get_assessment_repo),
    score_repo: ScoreRepository = Depends(get_score_repo)
):
    """
    Get assessment by ID
    """
    assessment = assessment_repo.get_by_id(assessment_id)
    if not assessment:
        raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))
    
    verify_user_access(assessment.user_id, current_user)
    
    # Get scores
    scores = score_repo.get_assessment_scores(assessment_id)
    
    assessment_dict = assessment.to_safe_dict()
    assessment_dict["scores"] = [ScoreResponse.model_validate(s) for s in scores]
    
    return AssessmentResponse(**assessment_dict)


@router.get("", response_model=PaginatedResponse)
async def list_user_assessments(
    user_id: int,
    pagination: PaginationParams = Depends(),
    status_filter: AssessmentStatus = None,
    current_user: User = Depends(get_current_user),
    assessment_repo: AssessmentRepository = Depends(get_assessment_repo)
):
    """
    List assessments for a user
    """
    verify_user_access(user_id, current_user)
    
    assessments = assessment_repo.get_user_assessments(
        user_id=user_id,
        limit=pagination.page_size,
        status=status_filter
    )
    
    # Count total for pagination
    all_assessments = assessment_repo.get_user_assessments(user_id=user_id, status=status_filter)
    total = len(all_assessments)
    
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 1
    
    return PaginatedResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1,
        items=[AssessmentListResponse.model_validate(a) for a in assessments]
    )


@router.put("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: int,
    request: AssessmentUpdate,
    current_user: User = Depends(get_current_user),
    assessment_repo: AssessmentRepository = Depends(get_assessment_repo)
):
    """
    Update an assessment
    """
    assessment = assessment_repo.get_by_id(assessment_id)
    if not assessment:
        raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))
    
    verify_user_access(assessment.user_id, current_user)
    
    update_data = request.model_dump(exclude_unset=True)
    updated = assessment_repo.update(assessment_id, **update_data)
    
    if not updated:
        raise ValidationError(message="Failed to update assessment")
    
    return AssessmentResponse.model_validate(updated)


@router.post("/{assessment_id}/complete", response_model=AssessmentResponse)
async def complete_assessment(
    assessment_id: int,
    request: AssessmentCompleteRequest,
    current_user: User = Depends(get_current_user),
    assessment_repo: AssessmentRepository = Depends(get_assessment_repo),
    score_repo: ScoreRepository = Depends(get_score_repo)
):
    """
    Complete an assessment with results and scores
    """
    assessment = assessment_repo.get_by_id(assessment_id)
    if not assessment:
        raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))
    
    verify_user_access(assessment.user_id, current_user)
    
    # Complete assessment
    success = assessment_repo.complete_assessment(
        assessment_id=assessment_id,
        risk_level=request.risk_level,
        primary_root_cause=request.primary_root_cause,
        root_cause_data=request.root_cause_data,
        model_version=request.model_version,
        model_confidence=request.model_confidence,
        processing_time_ms=request.processing_time_ms
    )
    
    if not success:
        raise ValidationError(message="Failed to complete assessment")
    
    # Create scores if provided
    if request.scores:
        for score_data in request.scores:
            score_repo.create_score(
                assessment_id=assessment_id,
                score_type=score_data.score_type,
                value=score_data.value,
                confidence=score_data.confidence,
                calculation_method=score_data.calculation_method,
                additional_data=score_data.additional_data
            )
    
    # Get updated assessment with scores
    updated_assessment = assessment_repo.get_by_id(assessment_id)
    scores = score_repo.get_assessment_scores(assessment_id)
    
    assessment_dict = updated_assessment.to_safe_dict()
    assessment_dict["scores"] = [ScoreResponse.model_validate(s) for s in scores]
    
    logger.info(f"Assessment {assessment_id} completed")
    
    return AssessmentResponse(**assessment_dict)


@router.post("/{assessment_id}/scores", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
async def add_score(
    assessment_id: int,
    request: ScoreCreate,
    current_user: User = Depends(get_current_user),
    assessment_repo: AssessmentRepository = Depends(get_assessment_repo),
    score_repo: ScoreRepository = Depends(get_score_repo)
):
    """
    Add a score to an assessment
    """
    assessment = assessment_repo.get_by_id(assessment_id)
    if not assessment:
        raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))
    
    verify_user_access(assessment.user_id, current_user)
    
    score = score_repo.create_score(
        assessment_id=assessment_id,
        score_type=request.score_type,
        value=request.value,
        confidence=request.confidence,
        calculation_method=request.calculation_method,
        additional_data=request.additional_data
    )
    
    if not score:
        raise ValidationError(message="Failed to create score")
    
    return ScoreResponse.model_validate(score)


@router.delete("/{assessment_id}", response_model=SuccessResponse)
async def delete_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    assessment_repo: AssessmentRepository = Depends(get_assessment_repo)
):
    """
    Delete an assessment (soft delete)
    """
    assessment = assessment_repo.get_by_id(assessment_id)
    if not assessment:
        raise NotFoundError(resource="Assessment", resource_id=str(assessment_id))
    
    verify_user_access(assessment.user_id, current_user)
    
    success = assessment_repo.delete(assessment_id)
    
    if success:
        return SuccessResponse(
            success=True,
            message="Assessment deleted successfully"
        )
    else:
        return SuccessResponse(
            success=False,
            message="Failed to delete assessment"
        )


@router.get("/statistics/overview", response_model=AssessmentStatistics)
async def get_assessment_statistics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    assessment_repo: AssessmentRepository = Depends(get_assessment_repo)
):
    """
    Get assessment statistics
    """
    stats = assessment_repo.get_assessment_statistics(days=days)
    
    return AssessmentStatistics(
        total_assessments=stats.get("total_assessments", 0),
        completed_assessments=stats.get("completed_assessments", 0),
        pending_assessments=stats.get("pending_assessments", 0),
        failed_assessments=stats.get("failed_assessments", 0),
        avg_processing_time_ms=stats.get("avg_processing_time_ms", 0),
        risk_distribution=stats.get("risk_distribution", {}),
        root_cause_distribution=stats.get("root_cause_distribution", {}),
        period_days=days
    )
