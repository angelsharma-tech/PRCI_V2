"""
Database Configuration for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

import os
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from utils.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration class"""
    
    # Database URLs
    sqlite_url: str = "sqlite:///./prci_v2.db"
    postgresql_url: Optional[str] = None
    
    # Connection settings
    echo: bool = False  # SQL logging
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # SQLite specific settings
    sqlite_check_same_thread: bool = False
    sqlite_timeout: int = 20
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create configuration from environment variables"""
        return cls(
            sqlite_url=os.getenv('DATABASE_URL', cls.sqlite_url),
            postgresql_url=os.getenv('POSTGRESQL_URL'),
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
            pool_size=int(os.getenv('DB_POOL_SIZE', cls.pool_size)),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', cls.max_overflow)),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', cls.pool_timeout)),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', cls.pool_recycle)),
            sqlite_check_same_thread=os.getenv('SQLITE_CHECK_SAME_THREAD', 'false').lower() == 'true',
            sqlite_timeout=int(os.getenv('SQLITE_TIMEOUT', cls.sqlite_timeout))
        )
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL based on availability"""
        if self.postgresql_url:
            logger.info("Using PostgreSQL database")
            return self.postgresql_url
        else:
            logger.info("Using SQLite database")
            return self.sqlite_url
    
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL"""
        return self.postgresql_url is not None
    
    def is_sqlite(self) -> bool:
        """Check if using SQLite"""
        return self.postgresql_url is None


class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig.from_env()
        self.engine = None
        self.SessionLocal = None
        self.Base = declarative_base()
        
    def initialize(self) -> None:
        """Initialize database engine and session factory"""
        try:
            database_url = self.config.get_database_url()
            
            # Create engine based on database type
            if self.config.is_sqlite():
                self.engine = create_engine(
                    database_url,
                    echo=self.config.echo,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": self.config.sqlite_check_same_thread,
                        "timeout": self.config.sqlite_timeout
                    }
                )
            else:  # PostgreSQL
                self.engine = create_engine(
                    database_url,
                    echo=self.config.echo,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_timeout=self.config.pool_timeout,
                    pool_recycle=self.config.pool_recycle
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"Database initialized: {database_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_tables(self) -> None:
        """Create all database tables"""
        try:
            if not self.engine:
                raise RuntimeError("Database not initialized. Call initialize() first.")
            
            self.Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self) -> None:
        """Drop all database tables (use with caution)"""
        try:
            if not self.engine:
                raise RuntimeError("Database not initialized. Call initialize() first.")
            
            self.Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
            
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        return self.SessionLocal()
    
    def close(self) -> None:
        """Close database connections"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_session() -> Session:
    """Get a database session (for dependency injection)"""
    return get_database_manager().get_session()


def initialize_database(config: DatabaseConfig = None) -> None:
    """Initialize the global database manager"""
    global _db_manager
    _db_manager = DatabaseManager(config)
    _db_manager.initialize()
    _db_manager.create_tables()
