"""
Schemas Package for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from .auth import (
    Token,
    TokenPayload,
    LoginRequest,
    RegisterRequest,
    PasswordResetRequest,
    PasswordChangeRequest
)
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfileResponse,
    UserListResponse
)
from .assessment import (
    AssessmentBase,
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentResponse,
    AssessmentListResponse,
    AssessmentCompleteRequest,
    ScoreBase,
    ScoreCreate,
    ScoreResponse
)
from .conversation import (
    ConversationBase,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    MessageBase,
    MessageCreate,
    MessageResponse,
    ConversationListResponse
)
from .intervention import (
    InterventionBase,
    InterventionCreate,
    InterventionUpdate,
    InterventionResponse,
    UserInterventionBase,
    UserInterventionCreate,
    UserInterventionUpdate,
    UserInterventionResponse,
    InterventionListResponse
)
from .report import (
    ReportBase,
    ReportCreate,
    ReportUpdate,
    ReportResponse,
    ReportListResponse,
    ReportGenerateRequest
)
from .common import (
    PaginationParams,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
    HealthCheckResponse
)

__all__ = [
    # Auth
    "Token", "TokenPayload", "LoginRequest", "RegisterRequest",
    "PasswordResetRequest", "PasswordChangeRequest",
    # User
    "UserBase", "UserCreate", "UserUpdate", "UserResponse",
    "UserProfileResponse", "UserListResponse",
    # Assessment
    "AssessmentBase", "AssessmentCreate", "AssessmentUpdate",
    "AssessmentResponse", "AssessmentListResponse", "AssessmentCompleteRequest",
    "ScoreBase", "ScoreCreate", "ScoreResponse",
    # Conversation
    "ConversationBase", "ConversationCreate", "ConversationUpdate",
    "ConversationResponse", "MessageBase", "MessageCreate", "MessageResponse",
    "ConversationListResponse",
    # Intervention
    "InterventionBase", "InterventionCreate", "InterventionUpdate",
    "InterventionResponse", "UserInterventionBase", "UserInterventionCreate",
    "UserInterventionUpdate", "UserInterventionResponse", "InterventionListResponse",
    # Report
    "ReportBase", "ReportCreate", "ReportUpdate", "ReportResponse",
    "ReportListResponse", "ReportGenerateRequest",
    # Common
    "PaginationParams", "PaginatedResponse", "ErrorResponse",
    "SuccessResponse", "HealthCheckResponse"
]
