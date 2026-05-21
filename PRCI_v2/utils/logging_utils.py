"""
Logging Utilities for PRCI v2
Phase 4.1 - Backend Stabilization & Architecture Refactor
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import json

from config import LOGS_DIR, LOGGING_CONFIG


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Setup comprehensive logging configuration
    """
    # Create logs directory if it doesn't exist
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    standard_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    detailed_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(standard_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(
            os.path.join(LOGS_DIR, log_file),
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    else:
        # Default file handler
        default_file_handler = logging.FileHandler(
            os.path.join(LOGS_DIR, "prci_app.log"),
            mode='a',
            encoding='utf-8'
        )
        default_file_handler.setLevel(logging.DEBUG)
        default_file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(default_file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    """
    return logging.getLogger(name)


def log_user_action(action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log user actions for analytics and debugging
    """
    logger = get_logger("user_actions")
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details or {}
    }
    
    logger.info(f"USER_ACTION: {json.dumps(log_entry)}")


def log_error(
    error: Exception,
    context: Optional[str] = None,
    user_id: Optional[str] = None
) -> None:
    """
    Log errors with context information
    """
    logger = get_logger("errors")
    
    error_info = {
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "user_id": user_id
    }
    
    logger.error(f"ERROR: {json.dumps(error_info)}", exc_info=True)


def log_performance(
    operation: str,
    duration: float,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log performance metrics
    """
    logger = get_logger("performance")
    
    perf_entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "duration_seconds": duration,
        "details": details or {}
    }
    
    logger.info(f"PERFORMANCE: {json.dumps(perf_entry)}")


def log_data_access(
    data_type: str,
    operation: str,
    record_count: Optional[int] = None,
    user_id: Optional[str] = None
) -> None:
    """
    Log data access for security and analytics
    """
    logger = get_logger("data_access")
    
    access_entry = {
        "timestamp": datetime.now().isoformat(),
        "data_type": data_type,
        "operation": operation,
        "record_count": record_count,
        "user_id": user_id
    }
    
    logger.info(f"DATA_ACCESS: {json.dumps(access_entry)}")


def log_model_inference(
    model_type: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    confidence: Optional[float] = None,
    processing_time: Optional[float] = None
) -> None:
    """
    Log model inference activities
    """
    logger = get_logger("model_inference")
    
    inference_entry = {
        "timestamp": datetime.now().isoformat(),
        "model_type": model_type,
        "input_summary": {k: type(v).__name__ for k, v in input_data.items()},
        "output_summary": {k: type(v).__name__ for k, v in output_data.items()},
        "confidence": confidence,
        "processing_time_ms": processing_time * 1000 if processing_time else None
    }
    
    logger.info(f"MODEL_INFERENCE: {json.dumps(inference_entry)}")


class PerformanceTimer:
    """
    Context manager for timing operations
    """
    
    def __init__(self, operation: str, details: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.details = details
        self.start_time = None
        self.logger = get_logger("performance")
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            log_performance(self.operation, duration, self.details)


def log_session_start(session_id: str, user_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Log session start
    """
    logger = get_logger("sessions")
    
    session_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "event": "session_start",
        "user_data": user_data or {}
    }
    
    logger.info(f"SESSION: {json.dumps(session_entry)}")


def log_session_end(session_id: str, session_duration: Optional[float] = None) -> None:
    """
    Log session end
    """
    logger = get_logger("sessions")
    
    session_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "event": "session_end",
        "duration_seconds": session_duration
    }
    
    logger.info(f"SESSION: {json.dumps(session_entry)}")


def log_api_call(
    endpoint: str,
    method: str,
    status_code: int,
    response_time: Optional[float] = None,
    error: Optional[str] = None
) -> None:
    """
    Log API calls (for future FastAPI integration)
    """
    logger = get_logger("api_calls")
    
    api_entry = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "response_time_ms": response_time * 1000 if response_time else None,
        "error": error
    }
    
    logger.info(f"API_CALL: {json.dumps(api_entry)}")


def cleanup_old_logs(days_to_keep: int = 30) -> None:
    """
    Clean up old log files
    """
    logger = get_logger("maintenance")
    
    try:
        current_time = datetime.now()
        
        for filename in os.listdir(LOGS_DIR):
            if filename.endswith('.log'):
                file_path = os.path.join(LOGS_DIR, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Remove files older than specified days
                if (current_time - file_time).days > days_to_keep:
                    os.remove(file_path)
                    logger.info(f"Removed old log file: {filename}")
    
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {e}")


def get_log_stats() -> Dict[str, Any]:
    """
    Get statistics about log files
    """
    stats = {
        "log_directory": LOGS_DIR,
        "total_files": 0,
        "total_size_mb": 0,
        "files": []
    }
    
    try:
        for filename in os.listdir(LOGS_DIR):
            if filename.endswith('.log'):
                file_path = os.path.join(LOGS_DIR, filename)
                file_size = os.path.getsize(file_path)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                stats["total_files"] += 1
                stats["total_size_mb"] += file_size / (1024 * 1024)
                
                stats["files"].append({
                    "name": filename,
                    "size_mb": file_size / (1024 * 1024),
                    "last_modified": file_time.isoformat()
                })
    
    except Exception as e:
        logger = get_logger("maintenance")
        logger.error(f"Error getting log stats: {e}")
    
    return stats


# Initialize logging on module import
def initialize_logging():
    """
    Initialize logging system
    """
    try:
        setup_logging()
        logger = get_logger(__name__)
        logger.info("PRCI v2 Logging system initialized")
        return True
    except Exception as e:
        print(f"Failed to initialize logging: {e}")
        return False


# Auto-initialize when module is imported
initialize_logging()
