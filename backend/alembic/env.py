"""
Alembic environment configuration for Ops-Center.

This file is responsible for:
- Connecting to the PostgreSQL database
- Configuring SQLAlchemy metadata
- Running migrations in online/offline mode
"""

from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the app directory to the Python path
app_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(app_dir))

# Import models to ensure all tables are registered
try:
    from database.models import Base, metadata
except ImportError:
    # If database module not in app dir, try loading from current directory
    from backend.database.models import Base, metadata

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for 'autogenerate' support
target_metadata = metadata


def get_database_url():
    """
    Get database URL from environment variables.

    Priority:
    1. SQLALCHEMY_DATABASE_URL (full URL)
    2. Individual components (POSTGRES_HOST, POSTGRES_USER, etc.)
    3. Default values (for local development)
    """
    # Check for full URL first
    db_url = os.getenv('SQLALCHEMY_DATABASE_URL')
    if db_url:
        return db_url

    # Build from components
    host = os.getenv('POSTGRES_HOST', 'unicorn-postgresql')
    port = os.getenv('POSTGRES_PORT', '5432')
    user = os.getenv('POSTGRES_USER', 'unicorn')
    password = os.getenv('POSTGRES_PASSWORD', 'unicorn')
    database = os.getenv('POSTGRES_DB', 'unicorn_db')

    return f'postgresql://{user}:{password}@{host}:{port}/{database}'


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
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
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Override the sqlalchemy.url with environment variable
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
