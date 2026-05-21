"""
Intervention Model for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, Enum, JSON
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class InterventionType(enum.Enum):
    """Intervention type enumeration"""
    MINDFULNESS = "mindfulness"
    ACTIVITY = "activity"
    SOCIAL = "social"
    PRODUCTIVITY = "productivity"
    THERAPEUTIC = "therapeutic"
    EDUCATIONAL = "educational"


class InterventionCategory(enum.Enum):
    """Intervention category enumeration"""
    COPING_STRATEGY = "coping_strategy"
    LIFESTYLE_CHANGE = "lifestyle_change"
    SKILL_BUILDING = "skill_building"
    SUPPORT_RESOURCE = "support_resource"


class InterventionStatus(enum.Enum):
    """Intervention status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class UserInterventionStatus(enum.Enum):
    """User intervention status enumeration"""
    RECOMMENDED = "recommended"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class Intervention(BaseModel):
    """
    Intervention model for storing intervention templates
    """
    __tablename__ = "interventions"
    
    # Intervention identification
    title = Column(
        String(255),
        nullable=False,
        comment="Intervention title"
    )
    
    description = Column(
        Text,
        nullable=False,
        comment="Intervention description"
    )
    
    # Classification
    intervention_type = Column(
        Enum(InterventionType),
        nullable=False,
        comment="Intervention type"
    )
    
    category = Column(
        Enum(InterventionCategory),
        nullable=False,
        comment="Intervention category"
    )
    
    # Target conditions
    target_root_causes = Column(
        JSON,
        nullable=True,
        comment="Target root causes in JSON format"
    )
    
    target_risk_levels = Column(
        JSON,
        nullable=True,
        comment="Target risk levels in JSON format"
    )
    
    target_score_ranges = Column(
        JSON,
        nullable=True,
        comment="Target score ranges in JSON format"
    )
    
    # Intervention details
    duration_minutes = Column(
        Integer,
        nullable=True,
        comment="Estimated duration in minutes"
    )
    
    difficulty_level = Column(
        Integer,
        default=1,
        nullable=False,
        comment="Difficulty level (1-5)"
    )
    
    priority = Column(
        Integer,
        default=3,
        nullable=False,
        comment="Priority level (1-5, 1=highest)"
    )
    
    # Content
    instructions = Column(
        Text,
        nullable=True,
        comment="Step-by-step instructions"
    )
    
    resources = Column(
        JSON,
        nullable=True,
        comment="Additional resources in JSON format"
    )
    
    # Effectiveness data
    effectiveness_score = Column(
        Float,
        nullable=True,
        comment="Average effectiveness score (1-5)"
    )
    
    completion_rate = Column(
        Float,
        nullable=True,
        comment="Historical completion rate (0.0-1.0)"
    )
    
    # Status
    status = Column(
        Enum(InterventionStatus),
        default=InterventionStatus.ACTIVE,
        nullable=False,
        comment="Intervention status"
    )
    
    # Metadata
    version = Column(
        String(20),
        default="1.0",
        nullable=False,
        comment="Intervention version"
    )
    
    evidence_based = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether intervention is evidence-based"
    )
    
    # Relationships
    user_interventions = relationship(
        "UserIntervention",
        back_populates="intervention",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Intervention(id={self.id}, title={self.title}, type={self.intervention_type})>"
    
    @property
    def is_active(self) -> bool:
        """Check if intervention is active"""
        return self.status == InterventionStatus.ACTIVE
    
    def is_suitable_for(self, root_cause: str = None, risk_level: str = None, 
                        score_value: float = None) -> bool:
        """Check if intervention is suitable for given conditions"""
        # Check root cause compatibility
        if root_cause and self.target_root_causes:
            target_causes = self.target_root_causes if isinstance(self.target_root_causes, list) else []
            if root_cause not in target_causes:
                return False
        
        # Check risk level compatibility
        if risk_level and self.target_risk_levels:
            target_risks = self.target_risk_levels if isinstance(self.target_risk_levels, list) else []
            if risk_level not in target_risks:
                return False
        
        # Check score range compatibility
        if score_value is not None and self.target_score_ranges:
            ranges = self.target_score_ranges if isinstance(self.target_score_ranges, list) else []
            if not any(r['min'] <= score_value <= r['max'] for r in ranges):
                return False
        
        return True
    
    def to_safe_dict(self) -> dict:
        """Convert to dictionary"""
        return self.to_dict()


class UserIntervention(BaseModel):
    """
    UserIntervention model for tracking user-specific interventions
    """
    __tablename__ = "user_interventions"
    
    # Relationships
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="Associated user ID"
    )
    
    intervention_id = Column(
        Integer,
        ForeignKey("interventions.id"),
        nullable=False,
        index=True,
        comment="Associated intervention ID"
    )
    
    # Assessment relationship (context)
    assessment_id = Column(
        Integer,
        ForeignKey("assessments.id"),
        nullable=True,
        index=True,
        comment="Context assessment ID"
    )
    
    # Status tracking
    status = Column(
        Enum(UserInterventionStatus),
        default=UserInterventionStatus.RECOMMENDED,
        nullable=False,
        comment="User intervention status"
    )
    
    # Timing
    recommended_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Recommendation timestamp"
    )
    
    accepted_at = Column(
        DateTime,
        nullable=True,
        comment="Acceptance timestamp"
    )
    
    started_at = Column(
        DateTime,
        nullable=True,
        comment="Start timestamp"
    )
    
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="Completion timestamp"
    )
    
    # Progress tracking
    progress_percentage = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Progress percentage (0.0-1.0)"
    )
    
    # User feedback
    user_rating = Column(
        Integer,
        nullable=True,
        comment="User rating (1-5)"
    )
    
    user_feedback = Column(
        Text,
        nullable=True,
        comment="User feedback text"
    )
    
    effectiveness_rating = Column(
        Integer,
        nullable=True,
        comment="Perceived effectiveness (1-5)"
    )
    
    # Personalization
    personalized_notes = Column(
        Text,
        nullable=True,
        comment="Personalized notes for user"
    )
    
    modifications = Column(
        JSON,
        nullable=True,
        comment="User modifications in JSON format"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="interventions"
    )
    
    intervention = relationship(
        "Intervention",
        back_populates="user_interventions"
    )
    
    def __repr__(self):
        return f"<UserIntervention(id={self.id}, user_id={self.user_id}, status={self.status})>"
    
    @property
    def is_recommended(self) -> bool:
        """Check if intervention is recommended"""
        return self.status == UserInterventionStatus.RECOMMENDED
    
    @property
    def is_accepted(self) -> bool:
        """Check if intervention is accepted"""
        return self.status == UserInterventionStatus.ACCEPTED
    
    @property
    def is_in_progress(self) -> bool:
        """Check if intervention is in progress"""
        return self.status == UserInterventionStatus.IN_PROGRESS
    
    @property
    def is_completed(self) -> bool:
        """Check if intervention is completed"""
        return self.status == UserInterventionStatus.COMPLETED
    
    @property
    def duration_days(self) -> int:
        """Calculate duration in days if completed"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).days
        return 0
    
    def accept(self):
        """Accept intervention"""
        self.status = UserInterventionStatus.ACCEPTED
        self.accepted_at = datetime.utcnow()
    
    def start(self):
        """Start intervention"""
        self.status = UserInterventionStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
    
    def complete(self, rating: int = None, feedback: str = None, effectiveness: int = None):
        """Complete intervention"""
        self.status = UserInterventionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 1.0
        
        if rating:
            self.user_rating = rating
        if feedback:
            self.user_feedback = feedback
        if effectiveness:
            self.effectiveness_rating = effectiveness
    
    def reject(self):
        """Reject intervention"""
        self.status = UserInterventionStatus.REJECTED
    
    def update_progress(self, percentage: float):
        """Update progress percentage"""
        self.progress_percentage = max(0.0, min(1.0, percentage))
        
        # Auto-update status based on progress
        if self.progress_percentage >= 1.0 and not self.is_completed:
            self.complete()
        elif self.progress_percentage > 0 and self.status == UserInterventionStatus.ACCEPTED:
            self.start()
    
    def to_safe_dict(self) -> dict:
        """Convert to dictionary with computed values"""
        data = self.to_dict()
        data['duration_days'] = self.duration_days
        return data
