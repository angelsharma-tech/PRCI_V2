"""
Report Model for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, Enum, JSON, LargeBinary
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class ReportType(enum.Enum):
    """Report type enumeration"""
    COMPREHENSIVE = "comprehensive"
    SUMMARY = "summary"
    TREND = "trend"
    INTERVENTION = "intervention"
    CUSTOM = "custom"


class ReportFormat(enum.Enum):
    """Report format enumeration"""
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class ReportStatus(enum.Enum):
    """Report status enumeration"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class Report(BaseModel):
    """
    Report model for storing generated reports
    """
    __tablename__ = "reports"
    
    # User relationship
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="Associated user ID"
    )
    
    # Report identification
    title = Column(
        String(255),
        nullable=False,
        comment="Report title"
    )
    
    report_type = Column(
        Enum(ReportType),
        nullable=False,
        comment="Report type"
    )
    
    format = Column(
        Enum(ReportFormat),
        nullable=False,
        comment="Report format"
    )
    
    # Report content
    content = Column(
        Text,
        nullable=True,
        comment="Report content (for text-based formats)"
    )
    
    file_data = Column(
        LargeBinary,
        nullable=True,
        comment="Binary file data (for PDF, etc.)"
    )
    
    file_path = Column(
        String(500),
        nullable=True,
        comment="File storage path"
    )
    
    file_size_bytes = Column(
        Integer,
        nullable=True,
        comment="File size in bytes"
    )
    
    # Report metadata
    description = Column(
        Text,
        nullable=True,
        comment="Report description"
    )
    
    parameters = Column(
        JSON,
        nullable=True,
        comment="Report generation parameters in JSON format"
    )
    
    # Data sources
    assessment_ids = Column(
        JSON,
        nullable=True,
        comment="Assessment IDs included in report"
    )
    
    date_range_start = Column(
        DateTime,
        nullable=True,
        comment="Report data start date"
    )
    
    date_range_end = Column(
        DateTime,
        nullable=True,
        comment="Report data end date"
    )
    
    # Generation metadata
    status = Column(
        Enum(ReportStatus),
        default=ReportStatus.PENDING,
        nullable=False,
        comment="Report generation status"
    )
    
    generation_time_ms = Column(
        Integer,
        nullable=True,
        comment="Generation time in milliseconds"
    )
    
    # Access control
    is_public = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether report is publicly accessible"
    )
    
    access_token = Column(
        String(255),
        nullable=True,
        unique=True,
        comment="Public access token"
    )
    
    expires_at = Column(
        DateTime,
        nullable=True,
        comment="Report expiration date"
    )
    
    # Sharing and delivery
    email_sent = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether report was sent via email"
    )
    
    email_sent_at = Column(
        DateTime,
        nullable=True,
        comment="Email sent timestamp"
    )
    
    download_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Download count"
    )
    
    last_accessed_at = Column(
        DateTime,
        nullable=True,
        comment="Last access timestamp"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="reports"
    )
    
    def __repr__(self):
        return f"<Report(id={self.id}, user_id={self.user_id}, type={self.report_type})>"
    
    @property
    def is_pending(self) -> bool:
        """Check if report is pending generation"""
        return self.status == ReportStatus.PENDING
    
    @property
    def is_generating(self) -> bool:
        """Check if report is currently generating"""
        return self.status == ReportStatus.GENERATING
    
    @property
    def is_completed(self) -> bool:
        """Check if report generation is completed"""
        return self.status == ReportStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if report generation failed"""
        return self.status == ReportStatus.FAILED
    
    @property
    def is_expired(self) -> bool:
        """Check if report has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB"""
        if self.file_size_bytes:
            return self.file_size_bytes / (1024 * 1024)
        return 0
    
    def start_generation(self):
        """Mark report as currently generating"""
        self.status = ReportStatus.GENERATING
    
    def complete_generation(self, file_data: bytes = None, file_path: str = None, 
                       generation_time_ms: int = None):
        """Mark report as completed"""
        self.status = ReportStatus.COMPLETED
        if file_data:
            self.file_data = file_data
            self.file_size_bytes = len(file_data)
        if file_path:
            self.file_path = file_path
        if generation_time_ms:
            self.generation_time_ms = generation_time_ms
    
    def fail_generation(self, error_message: str = None):
        """Mark report generation as failed"""
        self.status = ReportStatus.FAILED
        if error_message:
            self.description = error_message
    
    def mark_email_sent(self):
        """Mark report as sent via email"""
        self.email_sent = True
        self.email_sent_at = datetime.utcnow()
    
    def increment_download_count(self):
        """Increment download count and update last access"""
        self.download_count += 1
        self.last_accessed_at = datetime.utcnow()
    
    def generate_access_token(self) -> str:
        """Generate unique access token for public access"""
        import uuid
        self.access_token = str(uuid.uuid4())
        return self.access_token
    
    def set_expiration(self, days: int = 30):
        """Set report expiration date"""
        self.expires_at = datetime.utcnow() + timedelta(days=days)
    
    def is_accessible_by_token(self, token: str) -> bool:
        """Check if report is accessible by token"""
        return (self.access_token == token and 
                self.is_completed and 
                not self.is_expired and
                self.is_public)
    
    def to_safe_dict(self) -> dict:
        """Convert to dictionary with computed values"""
        data = self.to_dict(exclude_fields=['file_data'])  # Exclude binary data for safety
        data['file_size_mb'] = self.file_size_mb
        return data
