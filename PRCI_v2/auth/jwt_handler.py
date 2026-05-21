"""
JWT Handler for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from config import APP_SECURITY_CONFIG, DEV_CONFIG
from utils.logging_utils import get_logger

logger = get_logger(__name__)

# JWT Configuration
SECRET_KEY = APP_SECURITY_CONFIG.get("secret_key", "prci-v2-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = APP_SECURITY_CONFIG.get("session_timeout_hours", 24) * 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(
    user_id: int,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a new JWT access token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
        "type": "access"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Created access token for user {user_id}")
    return token


def create_refresh_token(
    user_id: int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a new JWT refresh token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
        "type": "refresh"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Created refresh token for user {user_id}")
    return token


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode an access token
    Returns the payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != "access":
            logger.warning("Invalid token type - expected access token")
            return None
        
        return payload
        
    except ExpiredSignatureError:
        logger.warning("Access token has expired")
        return None
    except InvalidTokenError as e:
        logger.warning(f"Invalid access token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying access token: {e}")
        return None


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a refresh token
    Returns the payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type - expected refresh token")
            return None
        
        return payload
        
    except ExpiredSignatureError:
        logger.warning("Refresh token has expired")
        return None
    except InvalidTokenError as e:
        logger.warning(f"Invalid refresh token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying refresh token: {e}")
        return None


def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    Get token payload without verification (for inspection)
    """
    try:
        # Decode without verification (for inspection only)
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False}
        )
        return payload
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        return None


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get token expiration time
    """
    payload = get_token_payload(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    return None


def is_token_expired(token: str) -> bool:
    """
    Check if a token is expired
    """
    expiry = get_token_expiry(token)
    if not expiry:
        return True
    return datetime.now(timezone.utc) > expiry


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Create a new access token using a valid refresh token
    """
    payload = verify_refresh_token(refresh_token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    # We would need to fetch user details from database here
    # For now, return a token that will be validated by the auth service
    # In production, you should fetch the user's current email and role
    return create_access_token(
        user_id=int(user_id),
        email="",  # Will be updated by auth service
        role=""    # Will be updated by auth service
    )
