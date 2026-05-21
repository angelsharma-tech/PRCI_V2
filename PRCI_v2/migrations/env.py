"""
Alembic environment configuration for PRCI v2
Phase 4.2 - Persistent Storage & User System Integration
"""

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine
from alembic import context

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Import models and database configuration
from models.base import Base
from db.config import DatabaseConfig

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """
    Get database URL from environment or config
    """
    # Try environment variable first
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        return database_url
    
    # Try PostgreSQL URL
    postgresql_url = os.getenv('POSTGRESQL_URL')
    if postgresql_url:
        return postgresql_url
    
    # Fall back to SQLite from config or default
    db_config = DatabaseConfig.from_env()
    return db_config.sqlite_url


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    
    # Get database URL
    database_url = get_database_url()
    
    # Create engine based on database type
    if database_url.startswith('sqlite'):
        engine = create_engine(
            database_url,
            poolclass=pool.StaticPool,
            connect_args={
                "check_same_thread": False,
                "timeout": 20
            }
        )
    else:
        engine = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    connection = engine.connect()

    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
