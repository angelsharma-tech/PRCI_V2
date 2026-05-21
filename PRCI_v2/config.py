"""
Centralized configuration for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
import json

# =========================================================
# PATHS & DATASETS
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "phase_3_data")
ROOT_CAUSE_DATASET = os.path.join(DATA_DIR, "raw/root_cause/procrastination_dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "legacy_model_pipeline/outputs/twohead")
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, "best.pt")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./prci_v2.db')
POSTGRESQL_URL = os.getenv('POSTGRESQL_URL', None)

# Database Connection Settings
DB_ECHO = os.getenv('DB_ECHO', 'false').lower() == 'true'
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
DB_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

# SQLite Specific Settings
SQLITE_CHECK_SAME_THREAD = os.getenv('SQLITE_CHECK_SAME_THREAD', 'false').lower() == 'true'
SQLITE_TIMEOUT = int(os.getenv('SQLITE_TIMEOUT', '20'))

# Database Directory Configuration
DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")

# =========================================================
# DATABASE CONFIGURATION FOR PHASE 4.2
# =========================================================

# Database Type Detection
def get_database_type():
    """Detect which database type is being used"""
    if POSTGRESQL_URL:
        return "postgresql"
    elif DATABASE_URL:
        if DATABASE_URL.startswith('postgresql://'):
            return "postgresql"
        elif DATABASE_URL.startswith('sqlite'):
            return "sqlite"
    return "sqlite"

# Database Connection Configuration
def get_database_config():
    """Get database configuration based on type"""
    db_type = get_database_type()
    
    if db_type == "postgresql":
        return {
            "url": POSTGRESQL_URL or DATABASE_URL,
            "pool_size": DB_POOL_SIZE,
            "max_overflow": DB_MAX_OVERFLOW,
            "pool_timeout": DB_POOL_TIMEOUT,
            "pool_recycle": DB_POOL_RECYCLE,
            "echo": DB_ECHO,
            "connect_args": {
                "connect_timeout": 10,
                "application_name": "prci_v2"
            }
        }
    else:  # SQLite
        return {
            "url": DATABASE_URL,
            "poolclass": "StaticPool",
            "connect_args": {
                "check_same_thread": not SQLITE_CHECK_SAME_THREAD,
                "timeout": SQLITE_TIMEOUT,
                "uri": True
            },
            "echo": DB_ECHO
        }

# Database Migration Configuration
MIGRATION_CONFIG = {
    "alembic_ini_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations", "alembic.ini"),
    "migrations_dir": os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations", "versions"),
    "auto_generate": True,
    "revision_environment": False
}

# Database Health Check Configuration
HEALTH_CHECK_CONFIG = {
    "connection_timeout": 5,
    "query_timeout": 10,
    "check_interval_minutes": 5
}

# Database Backup Configuration
BACKUP_CONFIG = {
    "enabled": os.getenv('ENABLE_AUTO_BACKUP', 'true').lower() == 'true',
    "backup_interval_hours": int(os.getenv('BACKUP_INTERVAL_HOURS', '24')),
    "retention_days": int(os.getenv('BACKUP_RETENTION_DAYS', '30')),
    "backup_dir": BACKUP_DIR,
    "compress_backups": os.getenv('COMPRESS_BACKUPS', 'true').lower() == 'true'
}

# Database Performance Configuration
PERFORMANCE_CONFIG = {
    "slow_query_threshold_ms": int(os.getenv('SLOW_QUERY_THRESHOLD_MS', '1000')),
    "connection_pool_size": DB_POOL_SIZE,
    "max_overflow": DB_MAX_OVERFLOW,
    "pool_timeout": DB_POOL_TIMEOUT,
    "pool_recycle": DB_POOL_RECYCLE,
    "statement_timeout": int(os.getenv('STATEMENT_TIMEOUT_MS', '30000')),
    "query_cache_size": int(os.getenv('QUERY_CACHE_SIZE', '1000'))
}

# Database Security Configuration
SECURITY_CONFIG = {
    "require_ssl": os.getenv('REQUIRE_SSL', 'false').lower() == 'true',
    "ssl_cert_path": os.getenv('SSL_CERT_PATH', ''),
    "ssl_key_path": os.getenv('SSL_KEY_PATH', ''),
    "ssl_ca_path": os.getenv('SSL_CA_PATH', ''),
    "connection_timeout": int(os.getenv('DB_CONNECTION_TIMEOUT', '10')),
    "idle_in_transaction_timeout": int(os.getenv('IDLE_IN_TRANSACTION_TIMEOUT', '60'))
}

# =========================================================
# RISK THRESHOLDS & COLORS
# =========================================================
RISK_COLORS = {
    "LOW": "#2E7D32",
    "MODERATE": "#EF6C00", 
    "HIGH": "#C62828"
}

SCORE_THRESHOLDS = {
    "depression": {
        "low": 0.33,
        "moderate": 0.66,
        "high": 1.0
    },
    "anxiety": {
        "low": 0.33,
        "moderate": 0.66,
        "high": 1.0
    },
    "overall": {
        "low": 0.25,
        "moderate": 0.5,
        "high": 0.75
    }
}

# =========================================================
# UI CONSTANTS & STYLING
# =========================================================
UI_COLORS = {
    "primary": "#00E5FF",
    "secondary": "#8B5CF6",
    "accent": "#EC4899",
    "success": "#84CC16",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "text_primary": "#FFFFFF",
    "text_muted": "#94A3B8",
    "glass_bg": "rgba(255, 255, 255, 0.03)",
    "glass_border": "rgba(255, 255, 255, 0.08)"
}

UI_SPACING = {
    "card_padding": "20px",
    "card_margin": "16px",
    "sidebar_padding": "10px",
    "header_margin": "2.5rem",
    "section_gap": "20px"
}

UI_BORDERS = {
    "card_radius": "22px",
    "button_radius": "12px",
    "icon_radius": "50%"
}

# =========================================================
# MODEL CONFIGURATION
# =========================================================
MODEL_CONFIG = {
    "default_type": "ovr_logreg",
    "available_types": ["ovr_logreg", "xgboost"],
    "conversation_max_history": 10,
    "tracker_window_size": 7,
    "model_versions": {
        "bert": {
            "base": "bert-base-uncased",
            "large": "bert-large-uncased",
            "latest": "bert-large-uncased"
        },
        "classification": {
            "logreg": "v1.0",
            "rf": "v1.0",
            "xgboost": "v1.0"
        }
    },
    "model_paths": {
        "bert_base": os.path.join(MODEL_DIR, "bert-base.pt"),
        "bert_large": os.path.join(MODEL_DIR, "bert-large.pt"),
        "logreg_v1": os.path.join(MODEL_DIR, "logreg_v1.joblib"),
        "xgboost_v1": os.path.join(MODEL_DIR, "xgboost_v1.model")
    },
    "inference_settings": {
        "max_sequence_length": 512,
        "batch_size": 32,
        "temperature": 0.7,
        "top_k": 5,
        "device": "cpu"
    },
    "training_settings": {
        "learning_rate": 0.001,
        "batch_size": 16,
        "epochs": 10,
        "validation_split": 0.2,
        "early_stopping_patience": 5
    }
}

# =========================================================
# PHASE 4.2 SPECIFIC CONFIGURATION
# =========================================================

# Database Integration Settings
DATABASE_INTEGRATION = {
    "enable_persistence": os.getenv('ENABLE_PERSISTENCE', 'true').lower() == 'true',
    "auto_migrate": os.getenv('AUTO_MIGRATE', 'true').lower() == 'true',
    "session_management": {
        "cleanup_interval_minutes": 30,
        "default_session_hours": 24,
        "extend_on_activity": True,
        "store_streamlit_state": True
    },
    "data_retention": {
        "assessments_days": int(os.getenv('ASSESSMENT_RETENTION_DAYS', '90')),
        "conversations_days": int(os.getenv('CONVERSATION_RETENTION_DAYS', '30')),
        "sessions_hours": int(os.getenv('SESSION_RETENTION_HOURS', '168')),
        "reports_days": int(os.getenv('REPORT_RETENTION_DAYS', '90'))
    }
}

# Legacy Support
LEGACY_SUPPORT = {
    "maintain_compatibility": True,
    "streamlit_state_integration": True,
    "file_based_dataset_fallback": True,
    "in_memory_caching": True
}

# API Configuration (for future FastAPI integration)
API_CONFIG = {
    "title": "PRCI v2 API",
    "description": "Mental Health Assessment and Intervention Platform",
    "version": "4.2.0",
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "enable_cors": os.getenv('ENABLE_CORS', 'false').lower() == 'true',
    "cors_origins": os.getenv('CORS_ORIGINS', '*').split(',') if os.getenv('CORS_ORIGINS') else ['http://localhost:3000', 'http://localhost:8501'],
    "api_rate_limit": int(os.getenv('API_RATE_LIMIT', '100')),
    "api_timeout_seconds": int(os.getenv('API_TIMEOUT_SECONDS', '30'))
}

# Email Configuration
EMAIL_CONFIG = {
    "smtp_server": os.getenv('SMTP_SERVER', 'localhost'),
    "smtp_port": int(os.getenv('SMTP_PORT', '587')),
    "smtp_username": os.getenv('SMTP_USERNAME', ''),
    "smtp_password": os.getenv('SMTP_PASSWORD', ''),
    "smtp_use_tls": os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
    "default_from_email": os.getenv('DEFAULT_FROM_EMAIL', 'noreply@prci.ai'),
    "default_from_name": "PRCI v2",
    "email_templates": {
        "assessment_complete": "Your assessment is ready",
        "report_generated": "Your report is ready for download",
        "intervention_recommended": "New intervention recommended"
    }
}

# Report Configuration
REPORT_CONFIG = {
    "max_file_size_mb": int(os.getenv('MAX_REPORT_SIZE_MB', '50')),
    "retention_days": int(os.getenv('REPORT_RETENTION_DAYS', '90')),
    "default_format": "pdf",
    "include_charts": True,
    "watermark_reports": True,
    "auto_generate_daily": os.getenv('AUTO_GENERATE_DAILY', 'false').lower() == 'true',
        "daily_report_time": os.getenv('DAILY_REPORT_TIME', '09:00'),  # HH:MM format
        "email_daily_reports": os.getenv('EMAIL_DAILY_REPORTS', 'false').lower() == 'true'
}

# Feature Flags
FEATURE_FLAGS = {
    "enable_email_reports": os.getenv('ENABLE_EMAIL_REPORTS', 'true').lower() == 'true',
    "enable_data_export": os.getenv('ENABLE_DATA_EXPORT', 'true').lower() == 'true',
    "enable_analytics": os.getenv('ENABLE_ANALYTICS', 'false').lower() == 'true',
    "enable_moderation": os.getenv('ENABLE_MODERATION', 'false').lower() == 'true',
    "enable_api_access": os.getenv('ENABLE_API_ACCESS', 'false').lower() == 'true',
    "enable_real_time_collaboration": (
        os.getenv("ENABLE_REAL_TIME_COLLABORATION", "false").lower() == "true"
    ),
    "enable_mobile_notifications": os.getenv('ENABLE_MOBILE_NOTIFICATIONS', 'false').lower() == 'true',
    "enable_offline_mode": os.getenv('ENABLE_OFFLINE_MODE', 'false').lower() == 'true'
}

# Database Performance Configuration
DB_PERFORMANCE_CONFIG = {
    "cache_ttl_seconds": int(os.getenv('CACHE_TTL_SECONDS', '300')),
    "max_concurrent_users": int(os.getenv('MAX_CONCURRENT_USERS', '100')),
    "session_cleanup_interval_minutes": int(os.getenv('SESSION_CLEANUP_INTERVAL_MINUTES', '30')),
    "database_connection_pool_size": DB_POOL_SIZE,
    "slow_query_threshold_ms": int(os.getenv('SLOW_QUERY_THRESHOLD_MS', '1000')),
    "statement_timeout_ms": int(os.getenv('STATEMENT_TIMEOUT_MS', '30000')),
    "query_cache_size": int(os.getenv('QUERY_CACHE_SIZE', '1000')),
    "enable_query_optimization": os.getenv('ENABLE_QUERY_OPTIMIZATION', 'true').lower() == 'true',
    "batch_processing": {
        "batch_size": int(os.getenv('BATCH_SIZE', '50')),
        "max_batch_size": int(os.getenv('MAX_BATCH_SIZE', '200'))
    }
}

# Application Security Configuration
APP_SECURITY_CONFIG = {
    "password_min_length": int(os.getenv('PASSWORD_MIN_LENGTH', '8')),
    "session_timeout_hours": int(os.getenv('SESSION_TIMEOUT_HOURS', '24')),
    "max_login_attempts": int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
    "lockout_duration_minutes": int(os.getenv('LOCKOUT_DURATION_MINUTES', '15')),
    "require_email_verification": os.getenv('REQUIRE_EMAIL_VERIFICATION', 'false').lower() == 'true',
    "enable_2fa": os.getenv('ENABLE_2FA', 'false').lower() == 'true',
    "session_encryption": os.getenv('SESSION_ENCRYPTION', 'true').lower() == 'true',
    "data_encryption": os.getenv('DATA_ENCRYPTION', 'false').lower() == 'true',
    "audit_log_retention_days": int(os.getenv('AUDIT_LOG_RETENTION_DAYS', '90'))
}

# Development Configuration
DEV_CONFIG = {
    "auto_create_tables": os.getenv('AUTO_CREATE_TABLES', 'true').lower() == 'true',
    "show_debug_info": os.getenv('SHOW_DEBUG_INFO', 'true').lower() == 'true',
    "enable_test_data": os.getenv('ENABLE_TEST_DATA', 'false').lower() == 'true',
    "debug_sql_queries": os.getenv('DEBUG_SQL_QUERIES', 'false').lower() == 'true',
    "enable_profiling": os.getenv('ENABLE_PROFILING', 'false').lower() == 'true',
    "mock_external_apis": os.getenv('MOCK_EXTERNAL_APIS', 'false').lower() == 'true'
}

# Monitoring and Observability
MONITORING_CONFIG = {
    "enable_metrics": os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
    "metrics_port": int(os.getenv('METRICS_PORT', '9090')),
    "health_check_interval_seconds": int(os.getenv('HEALTH_CHECK_INTERVAL_SECONDS', '60')),
    "log_level": os.getenv('LOG_LEVEL', 'INFO'),
    "structured_logging": os.getenv('STRUCTURED_LOGGING', 'true').lower() == 'true',
    "performance_monitoring": os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true',
    "error_tracking": os.getenv('ENABLE_ERROR_TRACKING', 'true').lower() == 'true'
}

# Integration Configuration
INTEGRATION_CONFIG = {
    "enable_legacy_compatibility": True,
    "streamlit_state_sync": True,
    "database_first": True,
    "cache_integration": True,
    "service_layer_isolation": True,
    "error_handling_centralized": True
}

# Testing Configuration
TESTING_CONFIG = {
    "test_database_url": os.getenv('TEST_DATABASE_URL', 'sqlite:///./test_prci_v2.db'),
    "test_data_file": os.getenv('TEST_DATA_FILE', 'test_data.json'),
    "enable_test_fixtures": os.getenv('ENABLE_TEST_FIXTURES', 'false').lower() == 'true',
    "mock_external_services": os.getenv('MOCK_EXTERNAL_SERVICES', 'false').lower() == 'true',
    "test_coverage_threshold": float(os.getenv('TEST_COVERAGE_THRESHOLD', '80.0'))
}

# =========================================================
# SVG ICONS
# =========================================================
SVG_ICONS = {
    "brain": """
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M9 3C6.79086 3 5 4.79086 5 7C5 7.72857 5.19483 8.41165 5.5359 9 C4.01458 9.52993 3 10.9785 3 12.6667C3 14.6424 4.35756 16.3025 6.1875 16.7647 C6.06683 17.0907 6 17.4432 6 17.8125C6 19.5726 7.42738 21 9.1875 21 C10.1994 21 11.1011 20.5285 11.6875 19.793V4.5C11.6875 3.67157 11.0159 3 10.1875 3H9Z" fill="#00E5FF"/>
<path d="M15 3C17.2091 3 19 4.79086 19 7C19 7.72857 18.8052 8.41165 18.4641 9 C19.9854 9.52993 21 10.9785 21 12.6667C21 14.6424 19.6424 16.3025 17.8125 16.7647 C17.9332 17.0907 18 17.4432 18 17.8125C18 19.5726 16.5726 21 14.8125 21 C13.8006 21 12.8989 20.5285 12.3125 19.793V4.5C12.3125 3.67157 12.9841 3 13.8125 3H15Z" fill="#8B5CF6"/>
</svg>
""",
    "core_ai_logo": """
<svg width="42" height="42" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="brainGlow" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#00E5FF"/><stop offset="100%" stop-color="#8B5CF6"/></linearGradient></defs>
<path d="M20 18C20 12 24 8 30 8C34 8 37 10 39 13 C41 11 44 10 48 10C55 10 60 15 60 22 C60 28 56 32 52 35C53 42 48 48 41 48 C37 48 34 46 32 43C30 46 27 48 23 48 C16 48 11 42 12 35C8 32 4 28 4 22 C4 15 9 10 16 10C18 10 19 10.5 20 11.5" stroke="url(#brainGlow)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M32 14V42M24 20L32 26L40 20 M22 32L32 38L42 32" stroke="url(#brainGlow)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
""",
    "depression": """
<svg width="28" height="28" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="sadGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#C084FC"/><stop offset="100%" stop-color="#7C3AED"/></linearGradient></defs>
<circle cx="32" cy="32" r="24" stroke="url(#sadGrad)" stroke-width="4"/><circle cx="24" cy="27" r="3" fill="#C084FC"/><circle cx="40" cy="27" r="3" fill="#C084FC"/><path d="M22 44C25 38 39 38 42 44" stroke="#C084FC" stroke-width="4" stroke-linecap="round"/></svg>
""",
    "anxiety": """
<svg width="28" height="28" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="brainGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#00E5FF"/><stop offset="100%" stop-color="#3B82F6"/></linearGradient></defs>
<path d="M24 10C17 10 12 15 12 22 C12 26 14 30 17 32 C16 38 20 44 27 44 C30 44 33 43 35 40 C37 43 40 44 43 44 C50 44 54 38 53 32 C56 30 58 26 58 22 C58 15 53 10 46 10 C42 10 38 12 35 15 C32 12 28 10 24 10Z" stroke="url(#brainGrad)" stroke-width="4" stroke-linejoin="round"/>
<path d="M24 22L30 28L26 34 M40 22L34 28L38 34" stroke="#00E5FF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>
""",
    "insight": """
<svg width="28" height="28" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="bulbGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#C084FC"/><stop offset="100%" stop-color="#8B5CF6"/></linearGradient></defs>
<path d="M32 10C22 10 14 18 14 28 C14 35 18 40 22 44 C24 46 25 48 25 50H39 C39 48 40 46 42 44 C46 40 50 35 50 28 C50 18 42 10 32 10Z" stroke="url(#bulbGrad)" stroke-width="4" stroke-linejoin="round"/>
<path d="M26 56H38" stroke="#C084FC" stroke-width="4" stroke-linecap="round"/></svg>
""",
    "run": """
<svg width="26" height="26" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="runGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#00E5FF"/><stop offset="100%" stop-color="#22D3EE"/></linearGradient></defs>
<circle cx="38" cy="12" r="5" fill="url(#runGrad)"/><path d="M30 22L40 28L46 20 M40 28L34 40 M34 40L24 50 M34 40L48 48 M28 26L22 36" stroke="url(#runGrad)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>
""",
    "shield": """
<svg width="26" height="26" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="shieldGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#A855F7"/><stop offset="100%" stop-color="#EC4899"/></linearGradient></defs>
<path d="M32 8L50 14V28 C50 40 42 50 32 56 C22 50 14 40 14 28V14L32 8Z" stroke="url(#shieldGrad)" stroke-width="4" stroke-linejoin="round"/>
<path d="M32 22V38 M24 30H40" stroke="#C084FC" stroke-width="4" stroke-linecap="round"/></svg>
""",
    "leaf": """
<svg width="24" height="24" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M52 12C30 12 14 26 14 44 C14 52 20 56 28 56 C46 56 52 40 52 12Z" stroke="#84CC16" stroke-width="4" stroke-linejoin="round"/><path d="M24 44C30 38 36 32 46 24" stroke="#84CC16" stroke-width="3" stroke-linecap="round"/></svg>
""",
    "heart": """
<svg width="24" height="24" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M32 54L10 32 C4 26 4 16 12 10 C18 6 26 8 32 16 C38 8 46 6 52 10 C60 16 60 26 54 32L32 54Z" stroke="#EC4899" stroke-width="4" stroke-linejoin="round"/></svg>
"""
}

# =========================================================
# INTERVENTION TEMPLATES
# =========================================================
INTERVENTION_TEMPLATES = {
    "procrastination": [
        "Replace quick scrolling with a planned short break after a sprint.",
        "Use app limits during study blocks.",
        "Set a 25-minute timer and commit to one task.",
        "Create a distraction-free workspace.",
        "Break large tasks into smaller, manageable chunks."
    ],
    "environment_distraction": [
        "Use noise-cancelling headphones or white noise.",
        "Turn off non-essential notifications.",
        "Designate a specific workspace for deep work.",
        "Use website blockers during focus time.",
        "Keep your workspace organized and clean."
    ],
    "fear_of_failure": [
        "Start with a 'good enough' version instead of perfect.",
        "Focus on progress over perfection.",
        "Celebrate small wins and learning moments.",
        "Practice self-compassion when things don't go as planned.",
        "Reframe failures as learning opportunities."
    ],
    "lack_of_interest": [
        "Connect the task to your personal values or goals.",
        "Try the Pomodoro technique with rewards.",
        "Find an accountability partner.",
        "Gamify the task with challenges or points.",
        "Switch to a more engaging approach or method."
    ],
    "dopamine_addiction": [
        "Schedule specific social media breaks.",
        "Use app timers and notifications.",
        "Replace one scrolling session with a walk.",
        "Practice delayed gratification techniques.",
        "Create a morning routine without screens."
    ],
    "burnout": [
        "Take regular micro-breaks throughout the day.",
        "Practice mindfulness or meditation for 5 minutes.",
        "Ensure you're getting adequate sleep.",
        "Delegate or say no to non-essential tasks.",
        "Engage in activities that recharge your energy."
    ],
    "anxiety": [
        "Practice deep breathing exercises for 2 minutes.",
        "Write down your worries to externalize them.",
        "Use the 5-4-3-2-1 grounding technique.",
        "Take a short walk to reset your mind.",
        "Challenge anxious thoughts with evidence."
    ],
    "depression": [
        "Reach out to a friend or family member.",
        "Engage in light physical activity.",
        "Practice gratitude journaling.",
        "Set one small, achievable goal for today.",
        "Ensure you're getting sunlight and fresh air."
    ],
    "perfectionism": [
        "Set 'good enough' standards for routine tasks.",
        "Time-box your work to prevent over-polishing.",
        "Ask for feedback early in the process.",
        "Focus on completion over perfection.",
        "Practice the 80/20 rule for prioritization."
    ]
}

# =========================================================
# INSIGHT TEMPLATES
# =========================================================
INSIGHT_TEMPLATES = {
    "low_risk_none": "You seem to be handling things well overall. Keep maintaining your current positive habits.",
    "default": "You seem a bit overwhelmed with {anxiety_level} anxiety and {depression_level} depressive signals. Your primary challenge appears to be {root_cause}. Consider taking small, consistent steps to address these patterns."
}

# =========================================================
# LOGGING CONFIGURATION
# =========================================================
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard"
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGS_DIR, "prci_app.log"),
            "formatter": "detailed",
            "mode": "a"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}
