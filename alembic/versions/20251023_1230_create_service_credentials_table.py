"""
Create service_credentials table for credential management

Revision ID: 20251023_1230
Revises:
Create Date: 2025-10-23 12:30:00.000000

This migration creates the service_credentials table for storing encrypted
service credentials (Cloudflare, NameCheap, GitHub, Stripe, etc.) with
proper indexing and unique constraints.

Epic 1.6/1.7: Service Credential Management
Author: Backend Development Team Lead
Date: October 23, 2025
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '20251023_1230'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Create service_credentials table

    Table Structure:
    - id: UUID primary key (auto-generated)
    - user_id: Keycloak user ID (from JWT/session)
    - service: Service name (cloudflare, namecheap, github, stripe)
    - credential_type: Credential type (api_token, api_key, client_secret)
    - encrypted_value: Fernet-encrypted credential
    - metadata: JSON metadata (description, test status, last tested date, etc.)
    - created_at: Creation timestamp with timezone
    - updated_at: Last update timestamp with timezone
    - last_tested: Last test timestamp with timezone
    - test_status: Test result (success, failed, error)
    - is_active: Soft delete flag
    """
    op.create_table(
        'service_credentials',

        # Primary key (UUID)
        sa.Column('id', UUID(as_uuid=False), primary_key=True, server_default=sa.text('gen_random_uuid()')),

        # User identification
        sa.Column('user_id', sa.String(255), nullable=False, index=True, comment='Keycloak user ID'),

        # Service identification
        sa.Column('service', sa.String(100), nullable=False, index=True, comment='Service name (cloudflare, namecheap, etc.)'),
        sa.Column('credential_type', sa.String(50), nullable=False, comment='Credential type (api_token, api_key, etc.)'),

        # Encrypted credential value
        sa.Column('encrypted_value', sa.Text(), nullable=False, comment='Fernet-encrypted credential'),

        # Metadata
        sa.Column('metadata', JSONB, nullable=True, comment='Additional metadata (description, test status, etc.)'),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),

        # Testing metadata
        sa.Column('last_tested', sa.TIMESTAMP(timezone=True), nullable=True, comment='Last time credential was tested'),
        sa.Column('test_status', sa.String(20), nullable=True, comment='Test result (success, failed, error)'),

        # Status
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False, index=True, comment='Soft delete flag'),

        # Unique constraint: one credential per user+service+type
        sa.UniqueConstraint('user_id', 'service', 'credential_type', name='uq_user_service_credential')
    )

    # Create indexes for common queries
    op.create_index('idx_service_creds_user', 'service_credentials', ['user_id'])
    op.create_index('idx_service_creds_service', 'service_credentials', ['service'])
    op.create_index('idx_service_creds_active', 'service_credentials', ['is_active'])
    op.create_index('idx_service_creds_user_service', 'service_credentials', ['user_id', 'service'])

    print("✅ service_credentials table created successfully")


def downgrade():
    """
    Drop service_credentials table and all indexes
    """
    # Drop indexes
    op.drop_index('idx_service_creds_user_service', table_name='service_credentials')
    op.drop_index('idx_service_creds_active', table_name='service_credentials')
    op.drop_index('idx_service_creds_service', table_name='service_credentials')
    op.drop_index('idx_service_creds_user', table_name='service_credentials')

    # Drop table
    op.drop_table('service_credentials')

    print("✅ service_credentials table dropped successfully")
