"""
Intervention Schemas for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from models.intervention import InterventionType, InterventionCategory, InterventionStatus, UserInterventionStatus


class InterventionBase(BaseModel):
    """Base intervention schema"""
    title: str = Field(min_length=1, max_length=255, description="Intervention title")
    description: str = Field(min_length=1, description="Intervention description")
    intervention_type: InterventionType = Field(description="Intervention type")
    category: InterventionCategory = Field(description="Intervention category")
    duration_minutes: Optional[int] = Field(default=None, ge=1, description="Estimated duration")
    difficulty_level: int = Field(default=1, ge=1, le=5, description="Difficulty level 1-5")
    priority: int = Field(default=5, ge=1, le=5, description="Priority 1-5 (1=highest)")
    instructions: Optional[str] = Field(default=None, description="Step-by-step instructions")
    resources: Optional[Dict[str, Any]] = Field(default=None, description="Additional resources")
    evidence_based: bool = Field(default=True, description="Evidence-based flag")


class InterventionCreate(InterventionBase):
    """Intervention creation schema"""
    target_root_causes: Optional[List[str]] = Field(default=None, description="Target root causes")
    target_risk_levels: Optional[List[str]] = Field(default=None, description="Target risk levels")
    target_score_ranges: Optional[Dict[str, Any]] = Field(default=None, description="Target score ranges")
    version: str = Field(default="1.0", description="Intervention version")


class InterventionUpdate(BaseModel):
    """Intervention update schema"""
    title: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    intervention_type: Optional[InterventionType] = Field(default=None)
    category: Optional[InterventionCategory] = Field(default=None)
    duration_minutes: Optional[int] = Field(default=None, ge=1)
    difficulty_level: Optional[int] = Field(default=None, ge=1, le=5)
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    instructions: Optional[str] = Field(default=None)
    resources: Optional[Dict[str, Any]] = Field(default=None)
    status: Optional[InterventionStatus] = Field(default=None)
    evidence_based: Optional[bool] = Field(default=None)


class InterventionResponse(InterventionBase):
    """Intervention response schema"""
    id: int = Field(description="Intervention ID")
    target_root_causes: Optional[List[str]] = Field(default=None, description="Target root causes")
    target_risk_levels: Optional[List[str]] = Field(default=None, description="Target risk levels")
    target_score_ranges: Optional[Dict[str, Any]] = Field(default=None, description="Target score ranges")
    effectiveness_score: Optional[float] = Field(default=None, description="Average effectiveness")
    completion_rate: Optional[float] = Field(default=None, description="Historical completion rate")
    status: InterventionStatus = Field(description="Intervention status")
    version: str = Field(description="Intervention version")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    
    model_config = ConfigDict(from_attributes=True)


class InterventionListResponse(BaseModel):
    """Intervention list response"""
    id: int
    title: str
    intervention_type: InterventionType
    category: InterventionCategory
    difficulty_level: int
    priority: int
    status: InterventionStatus
    effectiveness_score: Optional[float]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserInterventionBase(BaseModel):
    """Base user intervention schema"""
    status: UserInterventionStatus = Field(default=UserInterventionStatus.RECOMMENDED, description="Status")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress 0.0-1.0")


class UserInterventionCreate(UserInterventionBase):
    """User intervention creation schema"""
    user_id: int = Field(description="User ID")
    intervention_id: int = Field(description="Intervention ID")
    assessment_id: Optional[int] = Field(default=None, description="Context assessment ID")
    personalized_notes: Optional[str] = Field(default=None, description="Personalized notes")


class UserInterventionUpdate(BaseModel):
    """User intervention update schema"""
    status: Optional[UserInterventionStatus] = Field(default=None)
    progress_percentage: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    user_rating: Optional[int] = Field(default=None, ge=1, le=5)
    user_feedback: Optional[str] = Field(default=None)
    effectiveness_rating: Optional[int] = Field(default=None, ge=1, le=5)
    personalized_notes: Optional[str] = Field(default=None)
    modifications: Optional[Dict[str, Any]] = Field(default=None)


class UserInterventionResponse(UserInterventionBase):
    """User intervention response schema"""
    id: int = Field(description="User intervention ID")
    user_id: int = Field(description="User ID")
    intervention_id: int = Field(description="Intervention ID")
    assessment_id: Optional[int] = Field(default=None, description="Context assessment ID")
    recommended_at: datetime = Field(description="Recommended at")
    accepted_at: Optional[datetime] = Field(default=None, description="Accepted at")
    started_at: Optional[datetime] = Field(default=None, description="Started at")
    completed_at: Optional[datetime] = Field(default=None, description="Completed at")
    user_rating: Optional[int] = Field(default=None, description="User rating")
    user_feedback: Optional[str] = Field(default=None, description="User feedback")
    effectiveness_rating: Optional[int] = Field(default=None, description="Effectiveness rating")
    personalized_notes: Optional[str] = Field(default=None, description="Personalized notes")
    modifications: Optional[Dict[str, Any]] = Field(default=None, description="Modifications")
    intervention: Optional[InterventionResponse] = Field(default=None, description="Intervention details")
    created_at: datetime = Field(description="Created at")
    updated_at: datetime = Field(description="Updated at")
    
    model_config = ConfigDict(from_attributes=True)


class InterventionStatistics(BaseModel):
    """Intervention statistics"""
    total_interventions: int = Field(description="Total interventions")
    active_interventions: int = Field(description="Active interventions")
    total_recommendations: int = Field(description="Total recommendations")
    completion_rate: float = Field(description="Completion rate")
    avg_effectiveness: float = Field(description="Average effectiveness")
    avg_user_rating: float = Field(description="Average user rating")
