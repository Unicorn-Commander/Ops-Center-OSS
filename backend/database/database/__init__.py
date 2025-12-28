"""
Database package for Ops-Center.

This package contains:
- SQLAlchemy models (models.py)
- Database connection utilities
- Alembic migration support
"""

from .models import Base, metadata

__all__ = ['Base', 'metadata']
