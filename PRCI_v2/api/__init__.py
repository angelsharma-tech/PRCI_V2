"""
API Package for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from .main import create_app
from .dependencies import get_db, get_current_user, require_role
from .middleware import setup_middleware
from .exceptions import APIException, AuthenticationError, ValidationError, NotFoundError

__all__ = [
    "create_app",
    "get_db",
    "get_current_user",
    "require_role",
    "setup_middleware",
    "APIException",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError"
]
