"""
FastAPI Application for PRCI v2
Phase 4.3 - FastAPI Backend & Authentication Architecture
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from config import API_CONFIG, FEATURE_FLAGS, DEV_CONFIG
from utils.logging_utils import get_logger, PerformanceTimer

from .middleware import setup_middleware
from .exceptions import APIException
from .dependencies import close_db_connections

# Import all routers
from routers import auth_router, users_router, assessments_router
from routers import conversations_router, interventions_router, reports_router
from routers import admin_router, health_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup/shutdown events
    """
    # Startup
    logger.info("=" * 60)
    logger.info("PRCI v2 API Starting up...")
    logger.info("=" * 60)
    
    startup_time = time.time()
    
    try:
        # Initialize database connections
        from db.connection import initialize_database
        from db.config import DatabaseConfig
        
        db_config = DatabaseConfig.from_env()
        initialize_database(db_config)
        logger.info("Database connections initialized")
        
        # Verify database health
        from db.connection import get_session_manager
        session_manager = get_session_manager()
        if session_manager.check_connection():
            logger.info("Database health check: PASS")
        else:
            logger.warning("Database health check: FAIL - check configuration")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        if not DEV_CONFIG.get("ignore_startup_errors", False):
            raise
    
    elapsed = time.time() - startup_time
    logger.info(f"Startup completed in {elapsed:.3f}s")
    logger.info(f"API Docs available at: {API_CONFIG.get('docs_url', '/docs')}")
    
    yield
    
    # Shutdown
    logger.info("PRCI v2 API Shutting down...")
    try:
        close_db_connections()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    """
    app = FastAPI(
        title=API_CONFIG.get("title", "PRCI v2 API"),
        description=API_CONFIG.get("description", "Mental Health Assessment and Intervention Platform"),
        version=API_CONFIG.get("version", "4.3.0"),
        docs_url=API_CONFIG.get("docs_url", "/docs"),
        redoc_url=API_CONFIG.get("redoc_url", "/redoc"),
        openapi_url="/openapi.json",
        lifespan=lifespan,
        default_response_class=JSONResponse
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Include routers
    _include_routers(app)
    
    # Setup exception handlers
    _setup_exception_handlers(app)
    
    # Custom OpenAPI schema
    _setup_openapi(app)
    
    logger.info("FastAPI application created successfully")
    return app


def _include_routers(app: FastAPI) -> None:
    """
    Include all API routers
    """
    # Health check (no auth required)
    app.include_router(
        health_router,
        prefix="/health",
        tags=["Health"]
    )
    
    # Authentication (no auth required)
    app.include_router(
        auth_router,
        prefix="/auth",
        tags=["Authentication"]
    )
    
    # Users (auth required)
    app.include_router(
        users_router,
        prefix="/users",
        tags=["Users"]
    )
    
    # Assessments (auth required)
    app.include_router(
        assessments_router,
        prefix="/assessments",
        tags=["Assessments"]
    )
    
    # Conversations (auth required)
    app.include_router(
        conversations_router,
        prefix="/conversations",
        tags=["Conversations"]
    )
    
    # Interventions (auth required)
    app.include_router(
        interventions_router,
        prefix="/interventions",
        tags=["Interventions"]
    )
    
    # Reports (auth required)
    app.include_router(
        reports_router,
        prefix="/reports",
        tags=["Reports"]
    )
    
    # Admin (admin role required)
    app.include_router(
        admin_router,
        prefix="/admin",
        tags=["Admin"]
    )
    
    logger.info("All routers included")


def _setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup global exception handlers
    """
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        logger.warning(f"APIException: {exc.message} (status={exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": exc.timestamp.isoformat()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": str(exc) if DEV_CONFIG.get("show_debug_info", False) else None,
                "timestamp": time.time()
            }
        )


def _setup_openapi(app: FastAPI) -> None:
    """
    Setup custom OpenAPI schema
    """
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Add security scheme
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your JWT token"
            }
        }
        
        # Add global security requirement (optional - some endpoints don't need auth)
        # openapi_schema["security"] = [{"BearerAuth": []}]
        
        # Add API info extensions
        openapi_schema["info"]["x-logo"] = {
            "url": "/static/logo.png",
            "altText": "PRCI v2 Logo"
        }
        
        openapi_schema["externalDocs"] = {
            "description": "API Documentation",
            "url": "/docs"
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi


# Create application instance
app = create_app()
