"""
API Middleware for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

import time
import uuid
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from config import API_CONFIG, FEATURE_FLAGS, DEV_CONFIG
from utils.logging_utils import get_logger, PerformanceTimer

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses
    """
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            duration = time.time() - start_time
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"- {response.status_code} ({duration:.3f}s)"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"- ERROR ({duration:.3f}s): {str(e)}"
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware
    """
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self.requests = {
            ip: [t for t in timestamps if current_time - t < 60]
            for ip, timestamps in self.requests.items()
        }
        
        # Check rate limit
        if client_ip in self.requests:
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return Response(
                    content='{"error":"RATE_LIMIT_EXCEEDED","message":"Too many requests"}',
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": "60"}
                )
            self.requests[client_ip].append(current_time)
        else:
            self.requests[client_ip] = [current_time]
        
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


def setup_middleware(app: FastAPI) -> None:
    """
    Setup all middleware for the FastAPI application
    """
    # Request logging
    app.add_middleware(RequestLoggingMiddleware)
    logger.info("Request logging middleware enabled")
    
    # Rate limiting
    if FEATURE_FLAGS.get("enable_rate_limiting", True):
        rate_limit = API_CONFIG.get("api_rate_limit", 100)
        app.add_middleware(RateLimitMiddleware, requests_per_minute=rate_limit)
        logger.info(f"Rate limiting middleware enabled ({rate_limit}/min)")
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware enabled")
    
    # CORS
    if API_CONFIG.get("enable_cors", False):
        origins = API_CONFIG.get("cors_origins", ["http://localhost:3000", "http://localhost:8501"])
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID", "X-Response-Time"],
            max_age=600
        )
        logger.info(f"CORS middleware enabled for origins: {origins}")
    else:
        # Add CORS middleware with restrictive settings for same-origin
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:8501"],  # Streamlit default
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"]
        )
        logger.info("CORS middleware enabled for Streamlit integration")
