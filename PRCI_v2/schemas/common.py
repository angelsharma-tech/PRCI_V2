"""
Common Schemas for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Pagination query parameters"""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
    items: List[Any] = Field(description="List of items")


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(description="Error code")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class SuccessResponse(BaseModel):
    """Success response schema"""
    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class HealthCheckResponse(BaseModel):
    """Health check response schema"""
    status: str = Field(description="Overall health status")
    version: str = Field(description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    components: Optional[Dict[str, Any]] = Field(default=None, description="Component health details")


class AuditLogBase(BaseModel):
    """Base audit log schema"""
    action: str = Field(description="Action performed")
    entity_type: str = Field(description="Type of entity affected")
    entity_id: Optional[int] = Field(default=None, description="ID of entity affected")
    user_id: Optional[int] = Field(default=None, description="User who performed the action")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional action details")
    ip_address: Optional[str] = Field(default=None, description="IP address of the requester")
    user_agent: Optional[str] = Field(default=None, description="User agent of the requester")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Action timestamp")
