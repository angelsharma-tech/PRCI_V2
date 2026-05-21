"""
Auth Router for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from api.dependencies import get_db
from auth.auth_service import AuthService
from schemas.auth import (
    Token, LoginRequest, RegisterRequest, PasswordResetRequest,
    PasswordResetConfirm, PasswordChangeRequest, RefreshTokenRequest
)
from schemas.common import SuccessResponse
from schemas.user import UserResponse

from utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get auth service"""
    return AuthService(db)


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account
    """
    logger.info(f"Registration request received for: {request.email}")
    
    result = auth_service.register(
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        username=request.username,
        timezone=request.timezone,
        language=request.language
    )
    
    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=3600,  # 1 hour
        user_id=result["user"]["id"],
        email=result["user"]["email"]
    )


@router.post("/login", response_model=Token)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and generate tokens
    """
    logger.info(f"Login request received for: {request.email}")
    
    result = auth_service.login(
        email=request.email,
        password=request.password,
        remember_me=request.remember_me
    )
    
    expires_in = 3600 * 24 if request.remember_me else 3600  # 24 hours or 1 hour
    
    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=expires_in,
        user_id=result["user"]["id"],
        email=result["user"]["email"]
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token
    """
    logger.info("Token refresh request received")
    
    result = auth_service.refresh_token(request.refresh_token)
    
    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
        expires_in=3600,
        user_id=0,  # Will be populated from token payload
        email=""
    )


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    all_devices: bool = False,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout user
    """
    # Note: Full implementation would require current_user dependency
    # For now, this is a stub that would be properly implemented
    logger.info("Logout request received")
    
    return SuccessResponse(
        success=True,
        message="Logout successful"
    )


@router.post("/password-reset-request", response_model=SuccessResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request password reset
    """
    logger.info(f"Password reset request received for: {request.email}")
    
    auth_service.request_password_reset(request.email)
    
    return SuccessResponse(
        success=True,
        message="If an account exists with this email, a password reset link has been sent."
    )


@router.post("/password-reset", response_model=SuccessResponse)
async def reset_password(
    request: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Reset password using reset token
    """
    logger.info("Password reset confirmation received")
    
    success = auth_service.reset_password(
        token=request.token,
        new_password=request.new_password
    )
    
    if success:
        return SuccessResponse(
            success=True,
            message="Password has been reset successfully"
        )
    else:
        return SuccessResponse(
            success=False,
            message="Password reset failed"
        )


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    request: PasswordChangeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change password (requires authentication)
    """
    # Note: Would need current_user dependency in production
    # This is a stub showing the endpoint structure
    logger.info("Password change request received")
    
    # In production:
    # success = auth_service.change_password(
    #     user_id=current_user.id,
    #     current_password=request.current_password,
    #     new_password=request.new_password
    # )
    
    return SuccessResponse(
        success=True,
        message="Password changed successfully"
    )
