"""Create extensions marketplace tables

Revision ID: 20251101_extensions
Revises: f6570c470a28
Create Date: 2025-11-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251101_extensions'
down_revision = 'f6570c470a28'
branch_labels = None
depends_on = None


def upgrade():
    # Create add_on_categories table
    op.create_table(
        'add_on_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(255), nullable=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index('idx_addon_categories_slug', 'add_on_categories', ['slug'])

    # Create add_ons table
    op.create_table(
        'add_ons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('long_description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('base_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='usd'),
        sa.Column('stripe_product_id', sa.String(255), nullable=True),
        sa.Column('stripe_price_id', sa.String(255), nullable=True),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('icon_url', sa.String(500), nullable=True),
        sa.Column('screenshot_urls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('compatibility', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('download_url', sa.String(500), nullable=True),
        sa.Column('documentation_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('install_count', sa.Integer(), default=0),
        sa.Column('rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('review_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.ForeignKeyConstraint(['category_id'], ['add_on_categories.id'], ondelete='SET NULL')
    )
    op.create_index('idx_addons_slug', 'add_ons', ['slug'])
    op.create_index('idx_addons_category', 'add_ons', ['category_id'])
    op.create_index('idx_addons_active', 'add_ons', ['is_active'])
    op.create_index('idx_addons_featured', 'add_ons', ['is_featured'])

    # Create add_on_purchases table
    op.create_table(
        'add_on_purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('add_on_id', sa.Integer(), nullable=False),
        sa.Column('stripe_session_id', sa.String(255), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(255), nullable=True),
        sa.Column('amount_paid', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='usd'),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('promo_code', sa.String(100), nullable=True),
        sa.Column('discount_amount', sa.Numeric(10, 2), default=0),
        sa.Column('features_granted', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('refunded_at', sa.DateTime(), nullable=True),
        sa.Column('refund_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['add_on_id'], ['add_ons.id'], ondelete='CASCADE')
    )
    op.create_index('idx_purchases_user', 'add_on_purchases', ['user_id'])
    op.create_index('idx_purchases_addon', 'add_on_purchases', ['add_on_id'])
    op.create_index('idx_purchases_status', 'add_on_purchases', ['status'])
    op.create_index('idx_purchases_stripe_session', 'add_on_purchases', ['stripe_session_id'])

    # Create cart_items table
    op.create_table(
        'cart_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('add_on_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), default=1),
        sa.Column('added_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['add_on_id'], ['add_ons.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'add_on_id', name='unique_user_addon_cart')
    )
    op.create_index('idx_cart_user', 'cart_items', ['user_id'])

    # Create add_on_reviews table
    op.create_table(
        'add_on_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('add_on_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('is_verified_purchase', sa.Boolean(), default=False),
        sa.Column('helpful_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['add_on_id'], ['add_ons.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('add_on_id', 'user_id', name='unique_user_addon_review')
    )
    op.create_index('idx_reviews_addon', 'add_on_reviews', ['add_on_id'])

    # Seed initial categories
    op.execute("""
        INSERT INTO add_on_categories (name, slug, description, display_order) VALUES
        ('AI Models', 'ai-models', 'Additional AI models and fine-tunes', 1),
        ('Integrations', 'integrations', 'Third-party service integrations', 2),
        ('Development Tools', 'dev-tools', 'Developer tools and utilities', 3),
        ('Monitoring', 'monitoring', 'System monitoring and analytics', 4),
        ('Security', 'security', 'Security and compliance tools', 5),
        ('Workflow Automation', 'automation', 'Workflow automation and orchestration', 6),
        ('Storage & Backup', 'storage', 'Storage solutions and backup tools', 7),
        ('Communication', 'communication', 'Communication and collaboration tools', 8)
    """)


def downgrade():
    op.drop_table('add_on_reviews')
    op.drop_table('cart_items')
    op.drop_table('add_on_purchases')
    op.drop_table('add_ons')
    op.drop_table('add_on_categories')
