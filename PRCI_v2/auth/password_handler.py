"""
Password Handler for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext

from utils.logging_utils import get_logger

logger = get_logger(__name__)

# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Cost factor
)

# Password reset token storage (in production, use Redis or database)
_password_reset_tokens = {}


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    """
    try:
        hashed = pwd_context.hash(password)
        logger.info("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        if not result:
            logger.warning("Password verification failed")
        return result
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def is_password_strong(password: str) -> tuple[bool, str]:
    """
    Check if a password meets strength requirements
    Returns (is_strong, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if not any(c in string.punctuation for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"


def generate_password_reset_token(user_id: int, expires_hours: int = 24) -> str:
    """
    Generate a secure password reset token
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    
    _password_reset_tokens[token] = {
        "user_id": user_id,
        "expires_at": expires_at,
        "used": False
    }
    
    logger.info(f"Generated password reset token for user {user_id}")
    return token


def verify_password_reset_token(token: str) -> Optional[int]:
    """
    Verify a password reset token
    Returns user_id if valid, None otherwise
    """
    if token not in _password_reset_tokens:
        logger.warning("Password reset token not found")
        return None
    
    token_data = _password_reset_tokens[token]
    
    # Check if token is expired
    if datetime.now(timezone.utc) > token_data["expires_at"]:
        logger.warning("Password reset token expired")
        del _password_reset_tokens[token]
        return None
    
    # Check if token was already used
    if token_data["used"]:
        logger.warning("Password reset token already used")
        del _password_reset_tokens[token]
        return None
    
    return token_data["user_id"]


def mark_password_reset_token_used(token: str) -> bool:
    """
    Mark a password reset token as used
    """
    if token not in _password_reset_tokens:
        return False
    
    _password_reset_tokens[token]["used"] = True
    logger.info("Password reset token marked as used")
    return True


def cleanup_expired_tokens() -> int:
    """
    Clean up expired password reset tokens
    Returns number of tokens cleaned
    """
    current_time = datetime.now(timezone.utc)
    expired_tokens = [
        token for token, data in _password_reset_tokens.items()
        if current_time > data["expires_at"]
    ]
    
    for token in expired_tokens:
        del _password_reset_tokens[token]
    
    if expired_tokens:
        logger.info(f"Cleaned up {len(expired_tokens)} expired password reset tokens")
    
    return len(expired_tokens)


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a secure random password
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        is_strong, _ = is_password_strong(password)
        if is_strong:
            return password
