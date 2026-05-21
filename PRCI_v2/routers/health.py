"""
Health Router for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_db
from schemas.common import HealthCheckResponse, SuccessResponse
from utils.logging_utils import get_logger

import time

logger = get_logger(__name__)

router = APIRouter()

# Health check start time for uptime calculation
START_TIME = time.time()


@router.get("", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Basic health check endpoint
    """
    uptime = time.time() - START_TIME
    
    # Check database connection
    db_healthy = False
    try:
        from db.connection import get_session_manager
        session_manager = get_session_manager()
        db_healthy = session_manager.check_connection()
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
    
    status = "healthy" if db_healthy else "degraded"
    
    return HealthCheckResponse(
        status=status,
        version="4.3.0",
        components={
            "database": "healthy" if db_healthy else "unhealthy",
            "uptime_seconds": round(uptime, 2)
        }
    )


@router.get("/ready", response_model=SuccessResponse)
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check for Kubernetes/health probes
    """
    try:
        # Check database
        from db.connection import get_session_manager
        session_manager = get_session_manager()
        
        if not session_manager.check_connection():
            return SuccessResponse(
                success=False,
                message="Service not ready - database connection failed"
            )
        
        return SuccessResponse(
            success=True,
            message="Service is ready"
        )
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return SuccessResponse(
            success=False,
            message=f"Service not ready: {str(e)}"
        )


@router.get("/live", response_model=SuccessResponse)
async def liveness_check():
    """
    Liveness check for Kubernetes/health probes
    """
    return SuccessResponse(
        success=True,
        message="Service is alive"
    )
