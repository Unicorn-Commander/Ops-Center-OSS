"""Stripe lifecycle handling for add-on purchases."""

import logging
import os
from typing import Any, Dict, Optional

import asyncpg
import stripe

from keycloak_integration import get_user_by_email

logger = logging.getLogger(__name__)


async def _connect():
    return await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "unicorn-postgresql"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "unicorn"),
        password=os.getenv("POSTGRES_PASSWORD", "unicorn"),
        database=os.getenv("POSTGRES_DB", "unicorn_db"),
    )


class StripeWebhookHandler:
    async def handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("type")
        obj = event.get("data", {}).get("object", {})
        if event_type == "checkout.session.completed":
            return await self.handle_checkout_completed(obj)
        if event_type == "charge.refunded":
            return await self.handle_charge_refunded(obj)
        if event_type == "customer.subscription.deleted":
            return await self.handle_subscription_deleted(obj)
        return {"status": "ignored", "event_type": event_type}

    async def _resolve_org(self, user_id: str, email: str, conn) -> Optional[str]:
        row = await conn.fetchrow(
            """
            SELECT om.org_id::text
            FROM users u
            JOIN organization_members om ON om.user_id = u.id::text
            WHERE u.zitadel_id = $1 OR LOWER(u.email) = LOWER($2)
            ORDER BY om.is_default DESC, om.joined_at ASC
            LIMIT 1
            """,
            user_id,
            email,
        )
        if row:
            return row["org_id"]
        user = await get_user_by_email(email) if email else None
        raw_org = ((user or {}).get("attributes", {}).get("org_id") or [None])[0]
        return raw_org[4:] if raw_org and raw_org.startswith("org_") else raw_org

    async def handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        if session.get("payment_status") != "paid":
            return {"status": "ignored", "reason": "payment incomplete"}

        metadata = session.get("metadata", {}) or {}
        user_id = metadata.get("user_id") or session.get("client_reference_id")
        email = metadata.get("user_email") or session.get("customer_email")
        cart_ids = [value for value in metadata.get("cart_item_ids", "").split(",") if value]
        if not user_id or not email or not cart_ids:
            return {"status": "error", "reason": "missing add-on checkout metadata"}

        conn = await _connect()
        try:
            cart_items = await conn.fetch(
                """
                SELECT c.id, c.add_on_id, c.quantity, a.name, a.base_price, a.feature_key
                FROM cart_items c
                JOIN add_ons a ON a.id = c.add_on_id
                WHERE c.user_id = $1 AND c.id::text = ANY($2::text[])
                """,
                user_id,
                cart_ids,
            )
            if not cart_items:
                return {"status": "error", "reason": "cart items not found"}

            org_id = await self._resolve_org(user_id, email, conn)
            if not org_id:
                return {"status": "error", "reason": "organization not found"}

            purchase_ids = []
            async with conn.transaction():
                for item in cart_items:
                    purchase_id = await conn.fetchval(
                        """
                        INSERT INTO add_on_purchases (
                            user_id, org_id, add_on_id, amount, currency, status,
                            stripe_payment_id, stripe_session_id, stripe_subscription_id,
                            feature_key, activated_at, metadata
                        )
                        VALUES ($1, $2, $3, $4, $5, 'completed', $6, $7, $8, $9, NOW(), $10::jsonb)
                        ON CONFLICT (stripe_session_id, add_on_id)
                        DO UPDATE SET status = 'completed', revoked_at = NULL, activated_at = NOW()
                        RETURNING id::text
                        """,
                        user_id,
                        org_id,
                        item["add_on_id"],
                        item["base_price"] * item["quantity"],
                        (session.get("currency") or "usd").upper(),
                        session.get("payment_intent"),
                        session.get("id"),
                        session.get("subscription"),
                        item["feature_key"],
                        "{}",
                    )
                    purchase_ids.append(purchase_id)
                    await self._activate_addon(
                        conn, purchase_id, org_id, item["feature_key"], item["name"]
                    )
                await conn.execute(
                    "DELETE FROM cart_items WHERE user_id = $1 AND id::text = ANY($2::text[])",
                    user_id,
                    cart_ids,
                )
            return {"status": "activated", "org_id": org_id, "purchase_ids": purchase_ids}
        finally:
            await conn.close()

    async def _activate_addon(
        self, conn, purchase_id: str, org_id: str, feature_key: str, addon_name: str
    ):
        if not feature_key:
            raise ValueError(f"Add-on {addon_name} has no feature_key")
        await conn.execute(
            """
            INSERT INTO org_features (org_id, feature_key, enabled, granted_by, notes)
            VALUES ($1, $2, TRUE, 'stripe', $3)
            ON CONFLICT (org_id, feature_key)
            DO UPDATE SET enabled = TRUE, granted_by = 'stripe', notes = EXCLUDED.notes
            """,
            org_id,
            feature_key,
            f"Stripe add-on purchase {purchase_id}: {addon_name}",
        )

    async def handle_charge_refunded(self, charge: Dict[str, Any]) -> Dict[str, Any]:
        conn = await _connect()
        try:
            rows = await conn.fetch(
                """
                UPDATE add_on_purchases
                SET status = 'refunded', refunded_at = NOW(), revoked_at = NOW()
                WHERE stripe_payment_id = $1 AND status <> 'refunded'
                RETURNING id::text, org_id::text, add_on_id
                """,
                charge.get("payment_intent"),
            )
            async with conn.transaction():
                for row in rows:
                    await self._revoke_addon_access(conn, row["org_id"], row["add_on_id"])
            return {"status": "revoked", "purchase_count": len(rows)}
        finally:
            await conn.close()

    async def handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        conn = await _connect()
        try:
            rows = await conn.fetch(
                """
                UPDATE add_on_purchases
                SET status = 'refunded', revoked_at = NOW()
                WHERE stripe_subscription_id = $1 AND revoked_at IS NULL
                RETURNING id::text, org_id::text, add_on_id
                """,
                subscription.get("id"),
            )
            async with conn.transaction():
                for row in rows:
                    await self._revoke_addon_access(conn, row["org_id"], row["add_on_id"])
            return {"status": "revoked", "purchase_count": len(rows)}
        finally:
            await conn.close()

    async def _revoke_addon_access(self, conn, org_id: str, addon_id):
        feature_key = await conn.fetchval(
            "SELECT feature_key FROM add_ons WHERE id = $1", addon_id
        )
        if feature_key:
            await conn.execute(
                "UPDATE org_features SET enabled = FALSE WHERE org_id = $1 AND feature_key = $2",
                org_id,
                feature_key,
            )


webhook_handler = StripeWebhookHandler()
