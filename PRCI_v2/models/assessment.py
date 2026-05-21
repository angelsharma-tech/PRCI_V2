"""
Assessment Model for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, Enum, JSON
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class AssessmentType(enum.Enum):
    """Assessment type enumeration"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class AssessmentStatus(enum.Enum):
    """Assessment status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ScoreType(enum.Enum):
    """Score type enumeration"""
    DEPRESSION = "depression"
    ANXIETY = "anxiety"
    STRESS = "stress"
    OVERALL = "overall"


class Assessment(BaseModel):
    """
    Assessment model for storing mental health assessments
    """
    __tablename__ = "assessments"
    
    # User relationship
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="Associated user ID"
    )
    
    # Assessment metadata
    assessment_type = Column(
        Enum(AssessmentType),
        default=AssessmentType.AUTOMATIC,
        nullable=False,
        comment="Assessment type"
    )
    
    status = Column(
        Enum(AssessmentStatus),
        default=AssessmentStatus.PENDING,
        nullable=False,
        comment="Assessment status"
    )
    
    title = Column(
        String(255),
        nullable=True,
        comment="Assessment title"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Assessment description"
    )
    
    # Assessment input data
    input_text = Column(
        Text,
        nullable=True,
        comment="Input text for assessment"
    )
    
    input_data = Column(
        JSON,
        nullable=True,
        comment="Additional input data in JSON format"
    )
    
    # Model information
    model_version = Column(
        String(50),
        nullable=True,
        comment="Model version used for assessment"
    )
    
    model_confidence = Column(
        Float,
        nullable=True,
        comment="Model confidence score"
    )
    
    # Assessment results
    risk_level = Column(
        String(20),
        nullable=True,
        comment="Overall risk level"
    )
    
    primary_root_cause = Column(
        String(100),
        nullable=True,
        comment="Primary identified root cause"
    )
    
    root_cause_data = Column(
        JSON,
        nullable=True,
        comment="Root cause analysis data in JSON format"
    )
    
    # Assessment metadata
    processing_time_ms = Column(
        Integer,
        nullable=True,
        comment="Processing time in milliseconds"
    )
    
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="Assessment completion timestamp"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="assessments"
    )
    
    scores = relationship(
        "Score",
        back_populates="assessment",
        cascade="all, delete-orphan"
    )
    
    # Relationships from other models
    conversations = relationship(
        "Conversation",
        back_populates="current_assessment"
    )
    
    def __repr__(self):
        return f"<Assessment(id={self.id}, user_id={self.user_id}, status={self.status})>"
    
    @property
    def is_completed(self) -> bool:
        """Check if assessment is completed"""
        return self.status == AssessmentStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if assessment failed"""
        return self.status == AssessmentStatus.FAILED
    
    def complete(self, risk_level: str = None, root_cause: str = None):
        """Mark assessment as completed"""
        self.status = AssessmentStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if risk_level:
            self.risk_level = risk_level
        if root_cause:
            self.primary_root_cause = root_cause
    
    def fail(self, error_message: str = None):
        """Mark assessment as failed"""
        self.status = AssessmentStatus.FAILED
        if error_message:
            self.description = error_message
    
    def get_latest_scores(self) -> dict:
        """Get latest scores for this assessment"""
        if not self.scores:
            return {}
        
        # Group scores by type and get latest
        latest_scores = {}
        for score in self.scores:
            if score.score_type not in latest_scores or score.created_at > latest_scores[score.score_type].created_at:
                latest_scores[score.score_type] = score
        
        return {score_type.value: score for score_type, score in latest_scores.items()}
    
    def to_safe_dict(self) -> dict:
        """Convert to dictionary with score summaries"""
        data = self.to_dict()
        if self.scores:
            data['score_summary'] = {
                score.score_type.value: score.value
                for score in self.scores
            }
        return data


class Score(BaseModel):
    """
    Score model for storing individual assessment scores
    """
    __tablename__ = "scores"
    
    # Assessment relationship
    assessment_id = Column(
        Integer,
        ForeignKey("assessments.id"),
        nullable=False,
        index=True,
        comment="Associated assessment ID"
    )
    
    # Score data
    score_type = Column(
        Enum(ScoreType),
        nullable=False,
        comment="Score type"
    )
    
    value = Column(
        Float,
        nullable=False,
        comment="Score value (0.0-1.0)"
    )
    
    confidence = Column(
        Float,
        nullable=True,
        comment="Confidence score for this value"
    )
    
    # Score metadata
    calculation_method = Column(
        String(100),
        nullable=True,
        comment="Method used to calculate score"
    )
    
    additional_data = Column(
        JSON,
        nullable=True,
        comment="Additional score data in JSON format"
    )
    
    # Relationships
    assessment = relationship(
        "Assessment",
        back_populates="scores"
    )
    
    def __repr__(self):
        return f"<Score(id={self.id}, type={self.score_type}, value={self.value})>"
    
    @property
    def percentage(self) -> float:
        """Get score as percentage"""
        return self.value * 100
    
    @property
    def risk_category(self) -> str:
        """Get risk category based on score value"""
        if self.value < 0.33:
            return "LOW"
        elif self.value < 0.66:
            return "MODERATE"
        else:
            return "HIGH"
    
    def to_safe_dict(self) -> dict:
        """Convert to dictionary with computed values"""
        data = self.to_dict()
        data['percentage'] = self.percentage
        data['risk_category'] = self.risk_category
        return data
