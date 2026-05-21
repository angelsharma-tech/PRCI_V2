"""
Assessment Schemas for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from models.assessment import AssessmentType, AssessmentStatus, ScoreType


class ScoreBase(BaseModel):
    """Base score schema"""
    score_type: ScoreType = Field(description="Type of score")
    value: float = Field(ge=0.0, le=1.0, description="Score value (0.0-1.0)")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence score")
    calculation_method: Optional[str] = Field(default=None, description="Calculation method")
    additional_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")


class ScoreCreate(ScoreBase):
    """Score creation schema"""
    pass


class ScoreResponse(ScoreBase):
    """Score response schema"""
    id: int = Field(description="Score ID")
    assessment_id: int = Field(description="Assessment ID")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    
    model_config = ConfigDict(from_attributes=True)


class AssessmentBase(BaseModel):
    """Base assessment schema"""
    assessment_type: AssessmentType = Field(default=AssessmentType.AUTOMATIC, description="Assessment type")
    title: Optional[str] = Field(default=None, max_length=255, description="Assessment title")
    description: Optional[str] = Field(default=None, description="Assessment description")
    input_text: Optional[str] = Field(default=None, description="User input text")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="Structured input data")


class AssessmentCreate(AssessmentBase):
    """Assessment creation schema"""
    user_id: int = Field(description="User ID")
    model_version: Optional[str] = Field(default=None, description="AI model version")


class AssessmentUpdate(BaseModel):
    """Assessment update schema"""
    status: Optional[AssessmentStatus] = Field(default=None, description="Assessment status")
    risk_level: Optional[str] = Field(default=None, max_length=20, description="Risk level")
    primary_root_cause: Optional[str] = Field(default=None, max_length=100, description="Primary root cause")
    root_cause_data: Optional[Dict[str, Any]] = Field(default=None, description="Root cause analysis")
    model_version: Optional[str] = Field(default=None, description="Model version")
    model_confidence: Optional[float] = Field(default=None, description="Model confidence")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in ms")


class AssessmentCompleteRequest(BaseModel):
    """Assessment completion request"""
    risk_level: Optional[str] = Field(default=None, max_length=20, description="Risk level")
    primary_root_cause: Optional[str] = Field(default=None, max_length=100, description="Primary root cause")
    root_cause_data: Optional[Dict[str, Any]] = Field(default=None, description="Root cause data")
    model_version: Optional[str] = Field(default=None, description="Model version")
    model_confidence: Optional[float] = Field(default=None, description="Model confidence")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time")
    scores: Optional[List[ScoreCreate]] = Field(default=None, description="Scores to create")


class AssessmentResponse(AssessmentBase):
    """Assessment response schema"""
    id: int = Field(description="Assessment ID")
    user_id: int = Field(description="User ID")
    status: AssessmentStatus = Field(description="Assessment status")
    risk_level: Optional[str] = Field(default=None, description="Risk level")
    primary_root_cause: Optional[str] = Field(default=None, description="Primary root cause")
    root_cause_data: Optional[Dict[str, Any]] = Field(default=None, description="Root cause data")
    model_version: Optional[str] = Field(default=None, description="Model version")
    model_confidence: Optional[float] = Field(default=None, description="Model confidence")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    scores: List[ScoreResponse] = Field(default=[], description="Associated scores")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    
    model_config = ConfigDict(from_attributes=True)


class AssessmentListResponse(BaseModel):
    """Assessment list response"""
    id: int
    user_id: int
    assessment_type: AssessmentType
    status: AssessmentStatus
    title: Optional[str]
    risk_level: Optional[str]
    primary_root_cause: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime
    score_count: int = Field(default=0, description="Number of scores")
    
    model_config = ConfigDict(from_attributes=True)


class AssessmentStatistics(BaseModel):
    """Assessment statistics"""
    total_assessments: int = Field(description="Total assessments")
    completed_assessments: int = Field(description="Completed assessments")
    pending_assessments: int = Field(description="Pending assessments")
    failed_assessments: int = Field(description="Failed assessments")
    avg_processing_time_ms: float = Field(description="Average processing time")
    risk_distribution: Dict[str, int] = Field(description="Risk level distribution")
    root_cause_distribution: Dict[str, int] = Field(description="Root cause distribution")
    period_days: int = Field(description="Statistics period")
