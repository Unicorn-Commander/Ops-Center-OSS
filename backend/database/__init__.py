"""
Database package for Ops-Center.

This package contains:
- SQLAlchemy models (models.py)
- Database connection utilities
- Alembic migration support
"""

from .connection import get_db_pool, get_db_connection, close_db_pool

# Optional: Import models only if SQLAlchemy is available
try:
    from .models import Base, metadata
    __all__ = ['Base', 'metadata', 'get_db_pool', 'get_db_connection', 'close_db_pool']
except ImportError:
    __all__ = ['get_db_pool', 'get_db_connection', 'close_db_pool']
