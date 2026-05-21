"""
Routers Package for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from .auth import router as auth_router
from .users import router as users_router
from .assessments import router as assessments_router
from .conversations import router as conversations_router
from .interventions import router as interventions_router
from .reports import router as reports_router
from .admin import router as admin_router
from .health import router as health_router

__all__ = [
    "auth_router",
    "users_router",
    "assessments_router",
    "conversations_router",
    "interventions_router",
    "reports_router",
    "admin_router",
    "health_router"
]
