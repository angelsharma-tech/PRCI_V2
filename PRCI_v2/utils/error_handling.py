"""
Error Handling Utilities for PRCI v2
Phase 4.1 - Backend Stabilization & Architecture Refactor
"""

import os
import logging
import traceback
import functools
from typing import Any, Callable, Optional, Dict, Union, Type
from datetime import datetime

import pandas as pd

from config import UI_COLORS, LOGS_DIR
from utils.logging_utils import get_logger, log_error

logger = get_logger(__name__)


class PRCIError(Exception):
    """Base exception class for PRCI application"""
    pass


class DatasetError(PRCIError):
    """Raised when dataset operations fail"""
    pass


class ModelError(PRCIError):
    """Raised when model operations fail"""
    pass


class ChartError(PRCIError):
    """Raised when chart generation fails"""
    pass


class ReportError(PRCIError):
    """Raised when report generation fails"""
    pass


class EmailError(PRCIError):
    """Raised when email sending fails"""
    pass


class ValidationError(PRCIError):
    """Raised when input validation fails"""
    pass


def handle_dataset_errors(
    default_return: Any = None,
    should_log_error: bool = True,
    show_user_message: bool = True,
    user_message: str = "Dataset operation failed. Please try again."
):
    """
    Decorator for handling dataset-related errors
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                if should_log_error:
                    logger.error(f"Dataset file not found: {e}")
                if show_user_message:
                    import streamlit as st
                    st.error(f"Dataset file not found: {str(e)}")
                return default_return
            except pd.errors.EmptyDataError as e:
                if should_log_error:
                    logger.error(f"Dataset is empty: {e}")
                if show_user_message:
                    import streamlit as st
                    st.error("Dataset is empty or corrupted.")
                return default_return
            except pd.errors.ParserError as e:
                if should_log_error:
                    logger.error(f"Dataset parsing error: {e}")
                if show_user_message:
                    import streamlit as st
                    st.error("Dataset format is invalid.")
                return default_return
            except Exception as e:
                if should_log_error:
                    log_error(e, f"Dataset operation in {func.__name__}")
                if show_user_message:
                    import streamlit as st
                    st.error(user_message)
                return default_return
        return wrapper
    return decorator


def handle_model_errors(
    default_return: Any = None,
    should_log_error: bool = True,
    show_user_message: bool = True,
    user_message: str = "Model operation failed. Please check model configuration."
):
    """
    Decorator for handling model-related errors
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                if should_log_error:
                    logger.error(f"Model file not found: {e}")
                if show_user_message:
                    import streamlit as st
                    st.error(f"Model file not found: {str(e)}")
                return default_return
            except ImportError as e:
                if should_log_error:
                    logger.error(f"Model dependency missing: {e}")
                if show_user_message:
                    import streamlit as st
                    st.error("Required model dependencies are missing.")
                return default_return
            except MemoryError as e:
                if should_log_error:
                    logger.error(f"Model operation out of memory: {e}")
                if show_user_message:
                    import streamlit as st
                    st.error("Model operation requires more memory. Try using a smaller model.")
                return default_return
            except Exception as e:
                if should_log_error:
                    log_error(e, f"Model operation in {func.__name__}")
                if show_user_message:
                    import streamlit as st
                    st.error(user_message)
                return default_return
        return wrapper
    return decorator


def handle_chart_errors(
    default_return: Any = None,
    should_log_error: bool = True,
    show_user_message: bool = True,
    user_message: str = "Chart generation failed. Showing fallback visualization."
):
    """
    Decorator for handling chart-related errors
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                if should_log_error:
                    logger.error(f"Chart data validation error: {e}")
                if show_user_message:
                    import streamlit as st
                    st.warning("Chart data is invalid. Showing simplified view.")
                return _create_fallback_chart() if default_return is None else default_return
            except KeyError as e:
                if should_log_error:
                    logger.error(f"Chart configuration error: {e}")
                if show_user_message:
                    import streamlit as st
                    st.warning("Chart configuration is invalid.")
                return _create_fallback_chart() if default_return is None else default_return
            except Exception as e:
                if should_log_error:
                    log_error(e, f"Chart generation in {func.__name__}")
                if show_user_message:
                    import streamlit as st
                    st.error(user_message)
                return _create_fallback_chart() if default_return is None else default_return
        return wrapper
    return decorator


def handle_report_errors(
    default_return: Any = None,
    should_log_error: bool = True,
    show_user_message: bool = True,
    user_message: str = "Report generation failed. Please try again."
):
    """
    Decorator for handling report generation errors
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except PermissionError as e:
                if should_log_error:
                    logger.error(f"Report permission error: {e}")
                if show_user_message:
                    import streamlit as st
                    st.error("Permission denied when creating report. Check file permissions.")
                return default_return
            except OSError as e:
                if should_log_error:
                    logger.error(f"Report file system error: {e}")
                if show_user_message:
                    import streamlit as st
                    st.error("File system error when creating report.")
                return default_return
            except Exception as e:
                if should_log_error:
                    log_error(e, f"Report generation in {func.__name__}")
                if show_user_message:
                    import streamlit as st
                    st.error(user_message)
                return default_return
        return wrapper
    return decorator


def handle_email_errors(
    default_return: Any = False,
    should_log_error: bool = True,
    show_user_message: bool = True,
    user_message: str = "Email sending failed. Please check your email configuration."
):
    """
    Decorator for handling email sending errors
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ConnectionError as e:
                if should_log_error:
                    logger.error(f"Email connection error: {e}")
                if show_user_message:
                    import streamlit as st
                    st.error("Cannot connect to email server. Check your internet connection.")
                return default_return
            except TimeoutError as e:
                if should_log_error:
                    logger.error(f"Email timeout error: {e}")
                if show_user_message:
                    import streamlit as st
                    st.error("Email sending timed out. Please try again.")
                return default_return
            except Exception as e:
                if should_log_error:
                    log_error(e, f"Email sending in {func.__name__}")
                if show_user_message:
                    import streamlit as st
                    st.error(user_message)
                return default_return
        return wrapper
    return decorator


def validate_file_exists(file_path: str, error_message: Optional[str] = None) -> bool:
    """
    Validate that a file exists
    """
    if not os.path.exists(file_path):
        message = error_message or f"Required file not found: {file_path}"
        logger.error(message)
        raise FileNotFoundError(message)
    return True


def validate_directory_exists(dir_path: str, create_if_missing: bool = False) -> bool:
    """
    Validate that a directory exists
    """
    if not os.path.exists(dir_path):
        if create_if_missing:
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
                return True
            except OSError as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                raise
        else:
            message = f"Required directory not found: {dir_path}"
            logger.error(message)
            raise FileNotFoundError(message)
    return True


def validate_model_file(model_path: str) -> bool:
    """
    Validate model file integrity
    """
    try:
        validate_file_exists(model_path)
        
        # Check file size (should be reasonable for a model)
        file_size = os.path.getsize(model_path)
        if file_size < 1024:  # Less than 1KB is suspicious
            raise ModelError(f"Model file too small: {file_size} bytes")
        
        # Try to load basic model info (implementation depends on model type)
        logger.info(f"Model file validation passed: {model_path}")
        return True
        
    except Exception as e:
        logger.error(f"Model validation failed: {e}")
        raise ModelError(f"Model validation failed: {str(e)}")


def validate_dataset_file(dataset_path: str) -> bool:
    """
    Validate dataset file integrity
    """
    try:
        validate_file_exists(dataset_path)
        
        # Try to read a few lines to validate format
        import pandas as pd
        df = pd.read_csv(dataset_path, nrows=5)
        
        if df.empty:
            raise DatasetError("Dataset appears to be empty")
        
        # Check for required columns (basic validation)
        if len(df.columns) < 2:
            raise DatasetError("Dataset has insufficient columns")
        
        logger.info(f"Dataset validation passed: {dataset_path}")
        return True
        
    except Exception as e:
        logger.error(f"Dataset validation failed: {e}")
        raise DatasetError(f"Dataset validation failed: {str(e)}")


def safe_file_operation(operation: str, file_path: str, *args, **kwargs):
    """
    Safely perform file operations with error handling
    """
    try:
        if operation == "read":
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif operation == "write":
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                return f.write(*args, **kwargs)
        elif operation == "append":
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'a', encoding='utf-8') as f:
                return f.write(*args, **kwargs)
        else:
            raise ValueError(f"Unsupported file operation: {operation}")
            
    except Exception as e:
        logger.error(f"File operation {operation} failed for {file_path}: {e}")
        raise


def create_error_report(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a structured error report
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "context": context or {},
        "user_agent": _get_user_agent(),
        "environment": _get_environment_info()
    }


def _create_fallback_chart():
    """
    Create a fallback chart when chart generation fails
    """
    try:
        import plotly.graph_objects as go
        
        fig = go.Figure()
        fig.add_annotation(
            text="Chart temporarily unavailable",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color="white", size=16)
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Failed to create fallback chart: {e}")
        return None


def _get_user_agent() -> str:
    """
    Get user agent information
    """
    try:
        import streamlit as st
        return st.experimental_get_query_params().get('user_agent', ['unknown'])[0]
    except:
        return "unknown"


def _get_environment_info() -> Dict[str, Any]:
    """
    Get environment information for error reporting
    """
    return {
        "python_version": os.sys.version,
        "streamlit_version": st.__version__ if 'st' in globals() else "unknown",
        "platform": os.name,
        "working_directory": os.getcwd(),
        "log_directory": LOGS_DIR
    }


class ErrorRecovery:
    """
    Error recovery utilities
    """
    
    @staticmethod
    def retry_with_backoff(
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """
        Retry function with exponential backoff
        """
        for attempt in range(max_retries):
            try:
                return func()
            except exceptions as e:
                if attempt == max_retries - 1:
                    raise
                
                delay = base_delay * (backoff_factor ** attempt)
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
                import time
                time.sleep(delay)
    
    @staticmethod
    def graceful_degradation(
        primary_func: Callable,
        fallback_func: Callable,
        error_types: tuple = (Exception,)
    ) -> Any:
        """
        Attempt primary function, fall back to alternative on error
        """
        try:
            return primary_func()
        except error_types as e:
            logger.warning(f"Primary function failed, using fallback: {e}")
            try:
                return fallback_func()
            except Exception as fallback_error:
                logger.error(f"Both primary and fallback failed: {fallback_error}")
                raise


def safe_streamlit_operation(func: Callable, *args, **kwargs):
    """
    Safely execute Streamlit operations with error handling
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Streamlit operation failed: {e}")
        # Don't show error to user to avoid breaking the UI
        # Log it instead for debugging
        return None


# Global error handler setup
def setup_global_error_handling():
    """
    Setup global error handling for the application
    """
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Global exception handler"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Let KeyboardInterrupt pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Create error report
        error_report = create_error_report(exc_value, {
            "exception_type": exc_type.__name__,
            "uncaught": True
        })
        
        # Save error report to file
        try:
            error_file = os.path.join(LOGS_DIR, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            safe_file_operation("write", error_file, str(error_report))
        except:
            pass  # Don't let error reporting fail
    
    # Set global exception handler
    import sys
    sys.excepthook = handle_exception


# Initialize global error handling
setup_global_error_handling()
