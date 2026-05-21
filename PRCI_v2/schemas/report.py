"""
Report Schemas for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from models.report import ReportType, ReportFormat, ReportStatus


class ReportBase(BaseModel):
    """Base report schema"""
    title: str = Field(min_length=1, max_length=255, description="Report title")
    report_type: ReportType = Field(description="Report type")
    format: ReportFormat = Field(default=ReportFormat.PDF, description="Report format")
    description: Optional[str] = Field(default=None, description="Report description")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Generation parameters")
    date_range_start: Optional[datetime] = Field(default=None, description="Data start date")
    date_range_end: Optional[datetime] = Field(default=None, description="Data end date")


class ReportCreate(ReportBase):
    """Report creation schema"""
    user_id: int = Field(description="User ID")
    assessment_ids: Optional[List[int]] = Field(default=None, description="Assessment IDs to include")
    is_public: bool = Field(default=False, description="Public access flag")


class ReportUpdate(BaseModel):
    """Report update schema"""
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    is_public: Optional[bool] = Field(default=None)
    status: Optional[ReportStatus] = Field(default=None)


class ReportGenerateRequest(BaseModel):
    """Report generation request"""
    report_type: ReportType = Field(description="Report type")
    title: str = Field(min_length=1, max_length=255, description="Report title")
    format: ReportFormat = Field(default=ReportFormat.PDF, description="Report format")
    description: Optional[str] = Field(default=None, description="Report description")
    date_range_start: Optional[datetime] = Field(default=None, description="Data start date")
    date_range_end: Optional[datetime] = Field(default=None, description="Data end date")
    assessment_ids: Optional[List[int]] = Field(default=None, description="Assessment IDs to include")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Generation parameters")


class ReportResponse(ReportBase):
    """Report response schema"""
    id: int = Field(description="Report ID")
    user_id: int = Field(description="User ID")
    content: Optional[str] = Field(default=None, description="Report content")
    file_path: Optional[str] = Field(default=None, description="File path")
    file_size_bytes: Optional[int] = Field(default=None, description="File size")
    status: ReportStatus = Field(description="Report status")
    generation_time_ms: Optional[int] = Field(default=None, description="Generation time")
    is_public: bool = Field(description="Public access flag")
    access_token: Optional[str] = Field(default=None, description="Access token")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration date")
    email_sent: bool = Field(description="Email sent flag")
    email_sent_at: Optional[datetime] = Field(default=None, description="Email sent at")
    download_count: int = Field(description="Download count")
    last_accessed_at: Optional[datetime] = Field(default=None, description="Last accessed")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    completed_at: Optional[datetime] = Field(default=None, description="Completed at")
    
    model_config = ConfigDict(from_attributes=True)


class ReportListResponse(BaseModel):
    """Report list response"""
    id: int
    user_id: int
    title: str
    report_type: ReportType
    format: ReportFormat
    status: ReportStatus
    file_size_bytes: Optional[int]
    is_public: bool
    created_at: datetime
    completed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class ReportDownloadResponse(BaseModel):
    """Report download response"""
    report_id: int = Field(description="Report ID")
    download_url: str = Field(description="Download URL")
    expires_at: Optional[datetime] = Field(default=None, description="URL expiration")
    download_count: int = Field(description="Current download count")
