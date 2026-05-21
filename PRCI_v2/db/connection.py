"""
Database Connection Management for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DatabaseError, OperationalError

from .config import get_database_manager, DatabaseManager
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class DatabaseSessionManager:
    """Manages database sessions with proper error handling and cleanup"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or get_database_manager()
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with automatic cleanup
        
        Usage:
            with session_manager.get_session() as session:
                # Use session here
                result = session.query(Model).all()
        """
        session = None
        try:
            session = self.db_manager.get_session()
            yield session
            session.commit()
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            if session:
                session.close()
    
    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """
        Context manager for explicit transactions
        
        Usage:
            with session_manager.transaction() as session:
                # Multiple operations in single transaction
                obj1 = Model(field1=value1)
                obj2 = Model(field2=value2)
                session.add(obj1)
                session.add(obj2)
                # Auto commit on success, rollback on error
        """
        session = None
        try:
            session = self.db_manager.get_session()
            yield session
            session.commit()
            logger.debug("Transaction committed successfully")
        except (SQLAlchemyError, DatabaseError, OperationalError) as e:
            if session:
                session.rollback()
                logger.error(f"Database transaction rolled back: {e}")
            raise DatabaseError(f"Transaction failed: {str(e)}")
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Unexpected error in transaction: {e}")
            raise
        finally:
            if session:
                session.close()
    
    def execute_raw_sql(self, sql: str, params: dict = None) -> list:
        """
        Execute raw SQL with proper error handling
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            List of query results
        """
        try:
            with self.get_session() as session:
                result = session.execute(sql, params or {})
                return result.fetchall()
        except Exception as e:
            logger.error(f"Raw SQL execution failed: {sql}, error: {e}")
            raise DatabaseError(f"SQL execution failed: {str(e)}")


# Global session manager instance
_session_manager: Optional[DatabaseSessionManager] = None


def get_session_manager() -> DatabaseSessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = DatabaseSessionManager()
    return _session_manager


def get_db_session() -> Generator[Session, None, None]:
    """
    Convenience function to get a database session
    
    Usage:
        with get_db_session() as session:
            # Use session here
            result = session.query(Model).all()
    """
    return get_session_manager().get_session()


def with_db_session(func):
    """
    Decorator to automatically provide database session to functions
    
    Usage:
        @with_db_session
        def my_function(session, arg1, arg2):
            return session.query(Model).filter(Model.field == arg1).all()
    """
    def wrapper(*args, **kwargs):
        with get_db_session() as session:
            return func(session, *args, **kwargs)
    return wrapper


def with_transaction(func):
    """
    Decorator to automatically provide database transaction to functions
    
    Usage:
        @with_transaction
        def my_function(session, arg1, arg2):
            obj = Model(field=arg1)
            session.add(obj)
            return obj
    """
    def wrapper(*args, **kwargs):
        with get_session_manager().transaction() as session:
            return func(session, *args, **kwargs)
    return wrapper


class DatabaseHealthChecker:
    """Database health checking utilities"""
    
    def __init__(self, session_manager: DatabaseSessionManager = None):
        self.session_manager = session_manager or get_session_manager()
    
    def check_connection(self) -> dict:
        """
        Check database connection health
        
        Returns:
            Dictionary with health status information
        """
        try:
            with self.session_manager.get_session() as session:
                # Simple connection test
                session.execute("SELECT 1")
                
                return {
                    "status": "healthy",
                    "message": "Database connection successful",
                    "timestamp": logger.info("Database health check passed")
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "timestamp": str(logger)
            }
    
    def check_tables(self, table_names: list) -> dict:
        """
        Check if required tables exist
        
        Args:
            table_names: List of table names to check
            
        Returns:
            Dictionary with table existence information
        """
        results = {}
        
        try:
            with self.session_manager.get_session() as session:
                for table_name in table_names:
                    try:
                        session.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                        results[table_name] = True
                    except Exception:
                        results[table_name] = False
                
                missing_tables = [name for name, exists in results.items() if not exists]
                
                return {
                    "status": "healthy" if not missing_tables else "partial",
                    "tables": results,
                    "missing_tables": missing_tables,
                    "message": f"Tables check: {len(missing_tables)} missing"
                }
                
        except Exception as e:
            logger.error(f"Table health check failed: {e}")
            return {
                "status": "error",
                "message": f"Table check failed: {str(e)}"
            }
    
    def get_database_info(self) -> dict:
        """
        Get database information and statistics
        
        Returns:
            Dictionary with database information
        """
        try:
            with self.session_manager.get_session() as session:
                # Get database type and version
                if session.bind.dialect.name == 'sqlite':
                    version_result = session.execute("SELECT sqlite_version()").fetchone()
                    db_version = version_result[0] if version_result else "unknown"
                    db_type = "SQLite"
                else:
                    version_result = session.execute("SELECT version()").fetchone()
                    db_version = version_result[0] if version_result else "unknown"
                    db_type = "PostgreSQL"
                
                return {
                    "database_type": db_type,
                    "version": db_version,
                    "dialect": session.bind.dialect.name,
                    "driver": session.bind.driver,
                    "status": "connected"
                }
                
        except Exception as e:
            logger.error(f"Database info check failed: {e}")
            return {
                "status": "error",
                "message": f"Failed to get database info: {str(e)}"
            }
