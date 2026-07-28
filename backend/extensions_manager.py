"""
Extensions Marketplace Business Logic Manager

Handles all business logic for add-ons, cart, purchases, and feature grants.
This module separates business logic from API endpoints for better testing and reusability.

Author: Backend API Team Lead
Date: 2025-11-01
"""

import logging
import stripe
import asyncpg
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from database.connection import get_db_pool
from get_credential import get_credential

logger = logging.getLogger(__name__)

# Stripe Configuration
STRIPE_SECRET_KEY = get_credential("STRIPE_SECRET_KEY")
STRIPE_SUCCESS_URL = get_credential("STRIPE_SUCCESS_URL", "https://unicorncommander.ai/extensions/success")
STRIPE_CANCEL_URL = get_credential("STRIPE_CANCEL_URL", "https://unicorncommander.ai/extensions/cancel")

stripe.api_key = STRIPE_SECRET_KEY


class ExtensionsManager:
    """Business logic for Extensions Marketplace"""

    def __init__(self):
        self.pool = None

    async def initialize(self):
        """Initialize database pool"""
        self.pool = await get_db_pool()

    # ========================================================================
    # Catalog Operations
    # ========================================================================

    async def get_catalog(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get catalog of add-ons with filtering

        Returns:
            Tuple of (list of add-ons, total count)
        """
        if not self.pool:
            await self.initialize()

        query_conditions = ["is_active = TRUE", "is_public = TRUE"]
        query_params = []
        param_count = 1

        if category:
            query_conditions.append(f"category = ${param_count}")
            query_params.append(category)
            param_count += 1

        if search:
            query_conditions.append(f"(name ILIKE ${param_count} OR description ILIKE ${param_count})")
            query_params.append(f"%{search}%")
            param_count += 1

        where_clause = " AND ".join(query_conditions)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM add_ons WHERE {where_clause}"
        async with self.pool.acquire() as conn:
            total = await conn.fetchval(count_query, *query_params)

            # Get add-ons
            query = f"""
                SELECT id, name, slug, description, category, base_price, billing_type,
                       features, icon_url, is_featured, is_active, install_count,
                       rating_avg, rating_count, created_at, updated_at
                FROM add_ons
                WHERE {where_clause}
                ORDER BY is_featured DESC, install_count DESC, created_at DESC
                LIMIT ${param_count} OFFSET ${param_count + 1}
            """
            query_params.extend([limit, offset])

            rows = await conn.fetch(query, *query_params)
            add_ons = [dict(row) for row in rows]

        return add_ons, total

    async def get_addon_by_id(self, addon_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed add-on information by ID"""
        if not self.pool:
            await self.initialize()

        query = """
            SELECT * FROM add_ons
            WHERE id = $1 AND is_active = TRUE
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, str(addon_id))

        return dict(row) if row else None

    async def search_addons(
        self,
        query_str: str,
        category: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Full-text search for add-ons"""
        if not self.pool:
            await self.initialize()

        conditions = ["is_active = TRUE", "is_public = TRUE"]
        params = []
        param_count = 1

        # Full-text search
        if query_str:
            conditions.append(f"(name ILIKE ${param_count} OR description ILIKE ${param_count} OR long_description ILIKE ${param_count})")
            params.append(f"%{query_str}%")
            param_count += 1

        if category:
            conditions.append(f"category = ${param_count}")
            params.append(category)
            param_count += 1

        if min_price is not None:
            conditions.append(f"base_price >= ${param_count}")
            params.append(float(min_price))
            param_count += 1

        if max_price is not None:
            conditions.append(f"base_price <= ${param_count}")
            params.append(float(max_price))
            param_count += 1

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT id, name, slug, description, category, base_price, billing_type,
                   features, icon_url, is_featured, is_active, install_count,
                   rating_avg, rating_count, created_at, updated_at
            FROM add_ons
            WHERE {where_clause}
            ORDER BY
                CASE WHEN name ILIKE ${param_count} THEN 0 ELSE 1 END,
                rating_avg DESC,
                install_count DESC
            LIMIT ${param_count + 1}
        """
        params.extend([f"%{query_str}%", limit])

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    async def get_featured_addons(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Get featured add-ons"""
        if not self.pool:
            await self.initialize()

        query = """
            SELECT id, name, slug, description, category, base_price, billing_type,
                   features, icon_url, is_featured, is_active, install_count,
                   rating_avg, rating_count, created_at, updated_at
            FROM add_ons
            WHERE is_featured = TRUE AND is_active = TRUE AND is_public = TRUE
            ORDER BY rating_avg DESC, install_count DESC
            LIMIT $1
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [dict(row) for row in rows]

    async def get_recommended_addons(self, user_id: str, user_tier: str, limit: int = 6) -> List[Dict[str, Any]]:
        """Get recommended add-ons based on user's subscription tier"""
        if not self.pool:
            await self.initialize()

        # Simple recommendation: return top-rated add-ons that user doesn't own
        query = """
            SELECT DISTINCT a.id, a.name, a.slug, a.description, a.category, a.base_price,
                   a.billing_type, a.features, a.icon_url, a.is_featured, a.is_active,
                   a.install_count, a.rating_avg, a.rating_count, a.created_at, a.updated_at
            FROM add_ons a
            LEFT JOIN addon_purchases ap ON a.id = ap.add_on_id AND ap.user_id = $1 AND ap.is_active = TRUE
            WHERE a.is_active = TRUE AND a.is_public = TRUE AND ap.id IS NULL
            ORDER BY a.rating_avg DESC, a.install_count DESC
            LIMIT $2
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit)

        return [dict(row) for row in rows]

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories with add-on counts"""
        if not self.pool:
            await self.initialize()

        query = """
            SELECT category AS name,
                   COUNT(*) AS addon_count
            FROM add_ons
            WHERE is_active = TRUE AND is_public = TRUE
            GROUP BY category
            ORDER BY addon_count DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)

        # Add display names
        category_names = {
            'ai_tools': 'AI Tools',
            'monitoring': 'Monitoring',
            'storage': 'Storage',
            'security': 'Security',
            'networking': 'Networking',
            'analytics': 'Analytics',
            'integrations': 'Integrations',
            'utilities': 'Utilities',
            'other': 'Other'
        }

        return [
            {
                'name': row['name'],
                'display_name': category_names.get(row['name'], row['name'].replace('_', ' ').title()),
                'addon_count': row['addon_count'],
                'icon': None
            }
            for row in rows
        ]

    # ========================================================================
    # Cart Operations
    # ========================================================================

    async def get_cart(self, user_id: str, promo_code: Optional[str] = None) -> Dict[str, Any]:
        """Get user's cart with calculated totals"""
        if not self.pool:
            await self.initialize()

        query = """
            SELECT c.id, c.user_id, c.add_on_id, c.quantity, c.price_snapshot,
                   c.billing_type_snapshot, c.created_at,
                   a.id AS addon_id, a.name, a.slug, a.description, a.category,
                   a.base_price, a.billing_type, a.features, a.icon_url,
                   a.is_featured, a.is_active, a.install_count, a.rating_avg,
                   a.rating_count, a.created_at AS addon_created_at, a.updated_at
            FROM cart c
            JOIN add_ons a ON c.add_on_id = a.id
            WHERE c.user_id = $1 AND a.is_active = TRUE
            ORDER BY c.created_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)

        # Build cart items
        items = []
        subtotal = Decimal('0.00')

        for row in rows:
            item_price = Decimal(str(row['price_snapshot']))
            item_subtotal = item_price * row['quantity']
            subtotal += item_subtotal

            items.append({
                'id': row['id'],
                'add_on': {
                    'id': row['addon_id'],
                    'name': row['name'],
                    'slug': row['slug'],
                    'description': row['description'],
                    'category': row['category'],
                    'base_price': float(item_price),
                    'billing_type': row['billing_type'],
                    'features': row['features'],
                    'icon_url': row['icon_url'],
                    'is_featured': row['is_featured'],
                    'is_active': row['is_active'],
                    'install_count': row['install_count'],
                    'rating_avg': float(row['rating_avg']) if row['rating_avg'] else 0.0,
                    'rating_count': row['rating_count'],
                    'created_at': row['addon_created_at'],
                    'updated_at': row['updated_at']
                },
                'quantity': row['quantity'],
                'subtotal': float(item_subtotal),
                'created_at': row['created_at']
            })

        # Calculate discount
        discount = Decimal('0.00')
        promo_code_applied = None

        if promo_code:
            discount, promo_code_applied = await self._calculate_promo_discount(promo_code, subtotal)

        total = subtotal - discount

        return {
            'items': items,
            'subtotal': float(subtotal),
            'discount': float(discount),
            'total': float(total),
            'promo_code': promo_code_applied
        }

    async def add_to_cart(self, user_id: str, addon_id: UUID, quantity: int) -> Dict[str, Any]:
        """Add add-on to cart"""
        if not self.pool:
            await self.initialize()

        # Get add-on details
        addon = await self.get_addon_by_id(addon_id)
        if not addon:
            raise ValueError("Add-on not found or inactive")

        # Check if already in cart
        async with self.pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT id, quantity FROM cart WHERE user_id = $1 AND add_on_id = $2",
                user_id, str(addon_id)
            )

            if existing:
                # Update quantity
                new_quantity = existing['quantity'] + quantity
                await conn.execute(
                    "UPDATE cart SET quantity = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                    new_quantity, existing['id']
                )
            else:
                # Insert new item
                await conn.execute(
                    """
                    INSERT INTO cart (id, user_id, add_on_id, quantity, price_snapshot, billing_type_snapshot)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    str(uuid4()), user_id, str(addon_id), quantity,
                    float(addon['base_price']), addon['billing_type']
                )

        return await self.get_cart(user_id)

    async def remove_from_cart(self, user_id: str, cart_item_id: UUID) -> Dict[str, Any]:
        """Remove item from cart"""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM cart WHERE id = $1 AND user_id = $2",
                str(cart_item_id), user_id
            )

            if result == "DELETE 0":
                raise ValueError("Cart item not found")

        return await self.get_cart(user_id)

    async def update_cart_item(self, user_id: str, cart_item_id: UUID, quantity: int) -> Dict[str, Any]:
        """Update cart item quantity"""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE cart
                SET quantity = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2 AND user_id = $3
                """,
                quantity, str(cart_item_id), user_id
            )

            if result == "UPDATE 0":
                raise ValueError("Cart item not found")

        return await self.get_cart(user_id)

    async def clear_cart(self, user_id: str) -> bool:
        """Clear all items from cart"""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM cart WHERE user_id = $1", user_id)

        return True

    async def calculate_cart_total(self, user_id: str, promo_code: Optional[str] = None) -> Dict[str, Decimal]:
        """Calculate cart totals with optional promo code"""
        cart = await self.get_cart(user_id, promo_code)
        return {
            'subtotal': Decimal(str(cart['subtotal'])),
            'discount': Decimal(str(cart['discount'])),
            'total': Decimal(str(cart['total']))
        }

    async def _calculate_promo_discount(self, code: str, subtotal: Decimal) -> Tuple[Decimal, Optional[str]]:
        """Calculate discount from promo code"""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as conn:
            promo = await conn.fetchrow(
                """
                SELECT * FROM promo_codes
                WHERE code = $1
                  AND is_active = TRUE
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                  AND (max_uses IS NULL OR times_used < max_uses)
                """,
                code.upper()
            )

            if not promo:
                return Decimal('0.00'), None

            # Check minimum purchase amount
            if subtotal < Decimal(str(promo['min_purchase_amount'])):
                return Decimal('0.00'), None

            # Calculate discount
            discount = Decimal('0.00')
            if promo['discount_type'] == 'percentage':
                discount = subtotal * (Decimal(str(promo['discount_value'])) / Decimal('100'))
            elif promo['discount_type'] == 'fixed_amount':
                discount = Decimal(str(promo['discount_value']))

            # Ensure discount doesn't exceed subtotal
            discount = min(discount, subtotal)

            return discount, code.upper()

    # ========================================================================
    # Purchase Operations
    # ========================================================================

    async def create_stripe_checkout(
        self,
        user_id: str,
        cart_items: List[UUID],
        customer_email: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create Stripe Checkout Session for cart items"""
        if not self.pool:
            await self.initialize()

        # Get cart
        cart = await self.get_cart(user_id)

        # Filter cart items if specific IDs provided
        if cart_items:
            cart['items'] = [item for item in cart['items'] if UUID(item['id']) in cart_items]

        if not cart['items']:
            raise ValueError("No items in cart")

        # Create line items for Stripe
        line_items = []
        for item in cart['items']:
            addon = item['add_on']
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': addon['name'],
                        'description': addon['description'],
                        'images': [addon['icon_url']] if addon.get('icon_url') else []
                    },
                    'unit_amount': int(addon['base_price'] * 100),  # Convert to cents
                },
                'quantity': item['quantity']
            })

        # Create Stripe checkout session
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                customer_email=customer_email,
                metadata={
                    'user_id': user_id,
                    'addon_ids': ','.join(str(item['add_on']['id']) for item in cart['items'])
                },
                success_url=success_url or STRIPE_SUCCESS_URL,
                cancel_url=cancel_url or STRIPE_CANCEL_URL,
            )

            logger.info(f"Created Stripe checkout session {session.id} for user {user_id}")

            return {
                'checkout_url': session.url,
                'session_id': session.id,
                'amount': float(cart['total']),
                'currency': 'USD'
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout error: {e}")
            raise ValueError(f"Payment processing error: {str(e)}")

    async def get_user_purchases(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's purchase history"""
        if not self.pool:
            await self.initialize()

        conditions = ["ap.user_id = $1"]
        params = [user_id]
        param_count = 2

        if status:
            conditions.append(f"ap.status = ${param_count}")
            params.append(status)
            param_count += 1

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT ap.*, a.*
            FROM addon_purchases ap
            JOIN add_ons a ON ap.add_on_id = a.id
            WHERE {where_clause}
            ORDER BY ap.purchased_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([limit, offset])

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [dict(row) for row in rows]

    async def activate_purchase(self, purchase_id: UUID, user_id: str) -> Dict[str, Any]:
        """Activate purchased add-on and grant features"""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as conn:
            # Get purchase
            purchase = await conn.fetchrow(
                "SELECT * FROM addon_purchases WHERE id = $1 AND user_id = $2",
                str(purchase_id), user_id
            )

            if not purchase:
                raise ValueError("Purchase not found")

            if purchase['is_active']:
                return {
                    'success': True,
                    'purchase_id': purchase_id,
                    'features_granted': [],
                    'message': 'Purchase already activated'
                }

            # Grant features
            features = await self.grant_addon_features(user_id, UUID(purchase['add_on_id']))

            # Update purchase status
            await conn.execute(
                """
                UPDATE addon_purchases
                SET is_active = TRUE,
                    status = 'active',
                    activated_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """,
                str(purchase_id)
            )

            # Increment install count
            await conn.execute(
                "UPDATE add_ons SET install_count = install_count + 1 WHERE id = $1",
                purchase['add_on_id']
            )

            logger.info(f"Activated purchase {purchase_id} for user {user_id}")

            return {
                'success': True,
                'purchase_id': purchase_id,
                'features_granted': features,
                'message': 'Purchase activated successfully'
            }

    async def grant_addon_features(self, user_id: str, addon_id: UUID) -> List[str]:
        """Grant add-on features to user (placeholder - implement based on your feature system)"""
        if not self.pool:
            await self.initialize()

        # Get add-on features
        async with self.pool.acquire() as conn:
            features = await conn.fetch(
                "SELECT feature_key FROM addon_features WHERE add_on_id = $1",
                str(addon_id)
            )

        feature_keys = [f['feature_key'] for f in features]

        # TODO: Integrate with your feature grant system
        # This could update user_features table, Keycloak attributes, etc.
        logger.info(f"Granted features {feature_keys} to user {user_id}")

        return feature_keys

    async def get_user_active_addons(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active add-ons for user"""
        if not self.pool:
            await self.initialize()

        query = """
            SELECT ap.*, a.*
            FROM addon_purchases ap
            JOIN add_ons a ON ap.add_on_id = a.id
            WHERE ap.user_id = $1 AND ap.is_active = TRUE AND ap.status = 'active'
            ORDER BY ap.activated_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)

        active_addons = []
        for row in rows:
            # Get features
            features = await self._get_addon_features(UUID(row['add_on_id']))

            active_addons.append({
                'add_on': dict(row),
                'purchase': dict(row),
                'features': features
            })

        return active_addons

    async def _get_addon_features(self, addon_id: UUID) -> List[Dict[str, Any]]:
        """Get features for an add-on"""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT feature_key, feature_value FROM addon_features WHERE add_on_id = $1",
                str(addon_id)
            )

        return [{'key': row['feature_key'], 'value': row['feature_value']} for row in rows]

    # ========================================================================
    # Admin Operations
    # ========================================================================

    async def create_addon(self, addon_data: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        """Create new add-on (admin)"""
        if not self.pool:
            await self.initialize()

        addon_id = uuid4()

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO add_ons (
                    id, name, slug, description, long_description, category,
                    base_price, billing_type, trial_days, features, metadata,
                    icon_url, banner_url, documentation_url, support_url,
                    is_featured, is_active, is_public, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                """,
                str(addon_id), addon_data['name'], addon_data['slug'],
                addon_data.get('description'), addon_data.get('long_description'),
                addon_data['category'], float(addon_data['base_price']),
                addon_data['billing_type'], addon_data.get('trial_days', 0),
                addon_data.get('features', []), addon_data.get('metadata', {}),
                addon_data.get('icon_url'), addon_data.get('banner_url'),
                addon_data.get('documentation_url'), addon_data.get('support_url'),
                addon_data.get('is_featured', False), addon_data.get('is_active', True),
                addon_data.get('is_public', True), created_by
            )

        return await self.get_addon_by_id(addon_id)

    async def update_addon(self, addon_id: UUID, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update add-on (admin)"""
        if not self.pool:
            await self.initialize()

        # Build SET clause dynamically
        set_clauses = []
        params = []
        param_count = 1

        for key, value in updates.items():
            if value is not None:
                set_clauses.append(f"{key} = ${param_count}")
                params.append(value)
                param_count += 1

        if not set_clauses:
            return await self.get_addon_by_id(addon_id)

        set_clauses.append(f"updated_at = CURRENT_TIMESTAMP")
        set_clause = ", ".join(set_clauses)

        query = f"UPDATE add_ons SET {set_clause} WHERE id = ${param_count}"
        params.append(str(addon_id))

        async with self.pool.acquire() as conn:
            await conn.execute(query, *params)

        return await self.get_addon_by_id(addon_id)

    async def delete_addon(self, addon_id: UUID) -> bool:
        """Soft delete add-on (admin)"""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE add_ons SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE id = $1",
                str(addon_id)
            )

        return result == "UPDATE 1"

    async def get_analytics(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get sales analytics (admin)"""
        if not self.pool:
            await self.initialize()

        if not from_date:
            from_date = datetime.now() - timedelta(days=30)
        if not to_date:
            to_date = datetime.now()

        async with self.pool.acquire() as conn:
            # Total revenue
            total_revenue = await conn.fetchval(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM addon_purchases
                WHERE purchased_at BETWEEN $1 AND $2
                """,
                from_date, to_date
            )

            # Total sales
            total_sales = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM addon_purchases
                WHERE purchased_at BETWEEN $1 AND $2
                """,
                from_date, to_date
            )

            # Active subscriptions
            active_subs = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM addon_purchases
                WHERE is_active = TRUE AND billing_type IN ('monthly', 'annually')
                """
            )

            # Top sellers
            top_sellers = await conn.fetch(
                """
                SELECT a.name, a.slug, COUNT(ap.id) AS sales, SUM(ap.amount) AS revenue
                FROM addon_purchases ap
                JOIN add_ons a ON ap.add_on_id = a.id
                WHERE ap.purchased_at BETWEEN $1 AND $2
                GROUP BY a.id, a.name, a.slug
                ORDER BY revenue DESC
                LIMIT 10
                """,
                from_date, to_date
            )

            # Revenue by category
            revenue_by_category = await conn.fetch(
                """
                SELECT a.category, SUM(ap.amount) AS revenue
                FROM addon_purchases ap
                JOIN add_ons a ON ap.add_on_id = a.id
                WHERE ap.purchased_at BETWEEN $1 AND $2
                GROUP BY a.category
                ORDER BY revenue DESC
                """,
                from_date, to_date
            )

        return {
            'total_revenue': float(total_revenue) if total_revenue else 0.0,
            'total_sales': total_sales,
            'active_subscriptions': active_subs,
            'top_sellers': [dict(row) for row in top_sellers],
            'revenue_by_category': {row['category']: float(row['revenue']) for row in revenue_by_category}
        }

    async def create_promo_code(self, promo_data: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        """Create promotional code (admin)"""
        if not self.pool:
            await self.initialize()

        promo_id = uuid4()

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO promo_codes (
                    id, code, discount_type, discount_value, min_purchase_amount,
                    max_uses, applicable_addon_ids, expires_at, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                str(promo_id), promo_data['code'].upper(), promo_data['discount_type'],
                float(promo_data['discount_value']), float(promo_data.get('min_purchase_amount', 0)),
                promo_data.get('max_uses'), promo_data.get('applicable_addon_ids'),
                promo_data.get('expires_at'), created_by
            )

            # Get created promo code
            row = await conn.fetchrow("SELECT * FROM promo_codes WHERE id = $1", str(promo_id))

        return dict(row)
