"""
Reports Router for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from fastapi import APIRouter, Depends, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user, verify_user_access
from api.exceptions import NotFoundError, ValidationError

from models.user import User
from models.report import Report, ReportType, ReportFormat, ReportStatus
from repositories.report_repository import ReportRepository

from schemas.report import (
    ReportCreate, ReportUpdate, ReportResponse, ReportListResponse,
    ReportGenerateRequest, ReportDownloadResponse
)
from schemas.common import SuccessResponse, PaginatedResponse, PaginationParams

from utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_report_repo(db: Session = Depends(get_db)) -> ReportRepository:
    """Dependency to get report repository"""
    return ReportRepository(session=db)


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    request: ReportCreate,
    current_user: User = Depends(get_current_user),
    report_repo: ReportRepository = Depends(get_report_repo)
):
    """
    Create a new report
    """
    verify_user_access(request.user_id, current_user)
    
    report = report_repo.create_report(
        user_id=request.user_id,
        title=request.title,
        report_type=request.report_type,
        format=request.format,
        description=request.description,
        parameters=request.parameters,
        assessment_ids=request.assessment_ids,
        date_range_start=request.date_range_start,
        date_range_end=request.date_range_end
    )
    
    if not report:
        raise ValidationError(message="Failed to create report")
    
    return ReportResponse.model_validate(report)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    report_repo: ReportRepository = Depends(get_report_repo)
):
    """
    Get report by ID
    """
    report = report_repo.get_by_id(report_id)
    if not report:
        raise NotFoundError(resource="Report", resource_id=str(report_id))
    
    verify_user_access(report.user_id, current_user)
    
    return ReportResponse.model_validate(report)


@router.get("", response_model=PaginatedResponse)
async def list_user_reports(
    user_id: int,
    pagination: PaginationParams = Depends(),
    report_type: ReportType = None,
    format: ReportFormat = None,
    current_user: User = Depends(get_current_user),
    report_repo: ReportRepository = Depends(get_report_repo)
):
    """
    List reports for a user
    """
    verify_user_access(user_id, current_user)
    
    reports = report_repo.get_user_reports(
        user_id=user_id,
        report_type=report_type,
        format=format
    )
    
    # Pagination
    total = len(reports)
    start = (pagination.page - 1) * pagination.page_size
    end = start + pagination.page_size
    paginated_reports = reports[start:end]
    
    total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 1
    
    return PaginatedResponse(
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_prev=pagination.page > 1,
        items=[ReportListResponse.model_validate(r) for r in paginated_reports]
    )


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: int,
    request: ReportUpdate,
    current_user: User = Depends(get_current_user),
    report_repo: ReportRepository = Depends(get_report_repo)
):
    """
    Update a report
    """
    report = report_repo.get_by_id(report_id)
    if not report:
        raise NotFoundError(resource="Report", resource_id=str(report_id))
    
    verify_user_access(report.user_id, current_user)
    
    update_data = request.model_dump(exclude_unset=True)
    updated = report_repo.update(report_id, **update_data)
    
    if not updated:
        raise ValidationError(message="Failed to update report")
    
    return ReportResponse.model_validate(updated)


@router.post("/{report_id}/generate", response_model=ReportResponse)
async def generate_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    report_repo: ReportRepository = Depends(get_report_repo)
):
    """
    Generate a report (mark as generating)
    """
    report = report_repo.get_by_id(report_id)
    if not report:
        raise NotFoundError(resource="Report", resource_id=str(report_id))
    
    verify_user_access(report.user_id, current_user)
    
    success = report_repo.start_generation(report_id)
    if not success:
        raise ValidationError(message="Failed to start report generation")
    
    updated = report_repo.get_by_id(report_id)
    return ReportResponse.model_validate(updated)


@router.post("/{report_id}/complete", response_model=ReportResponse)
async def complete_report_generation(
    report_id: int,
    current_user: User = Depends(get_current_user),
    report_repo: ReportRepository = Depends(get_report_repo)
):
    """
    Complete report generation
    """
    report = report_repo.get_by_id(report_id)
    if not report:
        raise NotFoundError(resource="Report", resource_id=str(report_id))
    
    verify_user_access(report.user_id, current_user)
    
    # In production, this would receive file data
    success = report_repo.complete_generation(report_id)
    if not success:
        raise ValidationError(message="Failed to complete report generation")
    
    updated = report_repo.get_by_id(report_id)
    return ReportResponse.model_validate(updated)


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    report_repo: ReportRepository = Depends(get_report_repo)
):
    """
    Download a report
    """
    report = report_repo.get_by_id(report_id)
    if not report:
        raise NotFoundError(resource="Report", resource_id=str(report_id))
    
    verify_user_access(report.user_id, current_user)
    
    if report.status != ReportStatus.COMPLETED:
        raise ValidationError(message="Report is not ready for download")
    
    # Increment download count
    report_repo.increment_download_count(report_id)
    
    # Return file if available
    if report.file_data:
        return Response(
            content=report.file_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=report_{report_id}.{report.format.value.lower()}"
            }
        )
    else:
        # Return content if file data not stored
        return Response(
            content=report.content or "",
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=report_{report_id}.txt"
            }
        )


@router.post("/{report_id}/email", response_model=SuccessResponse)
async def email_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    report_repo: ReportRepository = Depends(get_report_repo)
):
    """
    Send report via email
    """
    report = report_repo.get_by_id(report_id)
    if not report:
        raise NotFoundError(resource="Report", resource_id=str(report_id))
    
    verify_user_access(report.user_id, current_user)
    
    success = report_repo.mark_email_sent(report_id)
    
    # In production, this would trigger an email service
    if success:
        return SuccessResponse(
            success=True,
            message="Report email sent successfully"
        )
    else:
        return SuccessResponse(
            success=False,
            message="Failed to send report email"
        )


@router.delete("/{report_id}", response_model=SuccessResponse)
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    report_repo: ReportRepository = Depends(get_report_repo)
):
    """
    Delete a report (soft delete)
    """
    report = report_repo.get_by_id(report_id)
    if not report:
        raise NotFoundError(resource="Report", resource_id=str(report_id))
    
    verify_user_access(report.user_id, current_user)
    
    success = report_repo.delete(report_id)
    
    if success:
        return SuccessResponse(
            success=True,
            message="Report deleted successfully"
        )
    else:
        return SuccessResponse(
            success=False,
            message="Failed to delete report"
        )
