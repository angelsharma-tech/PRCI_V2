"""
Auth Package for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from .jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    get_token_payload
)
from .password_handler import (
    hash_password,
    verify_password,
    generate_password_reset_token,
    verify_password_reset_token
)
from .auth_service import AuthService, get_auth_service

__all__ = [
    # JWT
    "create_access_token",
    "create_refresh_token",
    "verify_access_token",
    "verify_refresh_token",
    "get_token_payload",
    # Password
    "hash_password",
    "verify_password",
    "generate_password_reset_token",
    "verify_password_reset_token",
    # Service
    "AuthService",
    "get_auth_service"
]
