"""
Adversarial proof harness for the credit-purchase webhook idempotency fix.

Bug (pre-fix): /api/v1/billing/credits/webhook flipped credit_purchases.status to
'completed' WITHOUT a status predicate and then unconditionally called
allocate_credits() in a SEPARATE transaction. A Stripe duplicate/redelivery (routine)
double-granted credits; a mid-block exception 500'd and forced yet another retry.

Fix under proof:
  * credit_system.CreditManager.allocate_credits_on_conn() - grant on a caller-supplied
    connection so it participates in the caller's transaction (imported + executed FOR REAL
    below).
  * credit_purchase_api webhook - one connection, one transaction: SELECT ... FOR UPDATE,
    compare-and-swap on status, grant + status flip commit atomically, unknown session
    acked with 200 (no retry storm).

This harness imports the REAL allocate_credits_on_conn from credit_system.py and drives it
through process_credit_webhook(), whose transaction body is copied VERBATIM from the patched
credit_purchase_api.py webhook handler. Only audit_logger / email_notifications are stubbed
(best-effort logging that has no bearing on grant correctness).

Exit: 0 = all assertions pass, 1 = a proof assertion failed.
"""

import os
import sys
import asyncio
import tempfile
import textwrap
import uuid
from decimal import Decimal

# ---------------------------------------------------------------------------
# 1. Stub the heavy side-effect modules so the REAL credit_system imports cleanly.
#    (audit_logger / email_notifications = logging/email only; not grant logic.)
# ---------------------------------------------------------------------------
_stubdir = tempfile.mkdtemp(prefix="oc_stub_")
with open(os.path.join(_stubdir, "audit_logger.py"), "w") as f:
    f.write(textwrap.dedent("""
        class _AuditLogger:
            async def log(self, *a, **k):
                return None
            async def log_credit_purchase_initiated(self, *a, **k):
                return None
            async def log_credit_purchase_completed(self, *a, **k):
                return None
        audit_logger = _AuditLogger()
    """))
with open(os.path.join(_stubdir, "email_notifications.py"), "w") as f:
    f.write(textwrap.dedent("""
        class EmailNotificationService:
            async def send_welcome_email(self, *a, **k):
                return None
            async def send_low_balance_alert(self, *a, **k):
                return None
            async def send_monthly_reset_notification(self, *a, **k):
                return None
    """))

_BACKEND = os.environ.get("OC_BACKEND")
assert _BACKEND, "OC_BACKEND env (path to backend/) required"
sys.path.insert(0, _stubdir)       # stubs win over real audit_logger/email_notifications
sys.path.insert(1, _BACKEND)       # real credit_system.py

import asyncpg
from credit_system import credit_manager  # REAL module; allocate_credits_on_conn under test

DSN = os.environ["DATABASE_URL"]

FAIL = []
def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        FAIL.append(name)


# ---------------------------------------------------------------------------
# 2. Webhook transaction body - copied VERBATIM from the patched
#    credit_purchase_api.handle_stripe_webhook (checkout.session.completed branch).
#    The only harness-added hook is `fail_after_grant` to simulate a crash between the
#    grant and the status flip (the exact window the fix must make atomic).
# ---------------------------------------------------------------------------
class InjectedFailure(Exception):
    pass


async def process_credit_webhook(pool, session_id, user_id, credits, package_code,
                                 payment_intent, fail_after_grant=False):
    # Single connection + single transaction so the grant and the status flip commit
    # atomically. FOR UPDATE serializes concurrent duplicate deliveries.
    async with pool.acquire() as conn:
        async with conn.transaction():
            purchase = await conn.fetchrow(
                """
                SELECT id, status, amount_credits, package_name
                FROM credit_purchases
                WHERE stripe_checkout_session_id = $1
                FOR UPDATE
                """,
                session_id
            )

            if not purchase:
                return {"status": "ignored", "message": "Unknown checkout session"}
            elif purchase["status"] == "completed":
                return {"status": "already_processed"}
            else:
                await credit_manager.allocate_credits_on_conn(
                    conn,
                    user_id=user_id,
                    amount=Decimal(str(credits)),
                    source="purchase",
                    metadata={
                        "purchase_id": str(purchase["id"]),
                        "package_code": package_code,
                        "stripe_session_id": session_id,
                        "stripe_payment_intent": payment_intent,
                    },
                )

                if fail_after_grant:
                    # Simulate a crash AFTER the grant but BEFORE the status flip commits.
                    raise InjectedFailure("simulated crash mid-grant")

                await conn.execute(
                    """
                    UPDATE credit_purchases
                    SET status = 'completed',
                        completed_at = NOW(),
                        stripe_payment_intent_id = $1,
                        updated_at = NOW()
                    WHERE id = $2
                    """,
                    payment_intent,
                    purchase["id"],
                )
                return {"status": "success"}


# ---------------------------------------------------------------------------
# 3. Minimal schema matching the columns observed in the real DB access code.
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id uuid PRIMARY KEY
);

CREATE TABLE user_credits (
    user_id uuid PRIMARY KEY,
    balance numeric(18,2) DEFAULT 0,
    tier text DEFAULT 'trial',
    monthly_cap numeric(18,2) DEFAULT 0,
    monthly_usage numeric(18,2) DEFAULT 0,
    monthly_reset_at timestamptz,
    lifetime_credits numeric(18,2) DEFAULT 0,
    last_updated timestamptz DEFAULT now(),
    created_at timestamptz DEFAULT now()
);

CREATE TABLE credit_purchases (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id uuid,
    package_name text,
    amount_credits numeric(18,2),
    amount_paid numeric(18,2),
    stripe_checkout_session_id text UNIQUE,
    stripe_payment_intent_id text,
    stripe_payment_id text,
    status text,
    metadata jsonb,
    created_at timestamptz DEFAULT now(),
    completed_at timestamptz,
    updated_at timestamptz DEFAULT now()
);

CREATE TABLE transactions (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id uuid,
    type text,
    amount_cents bigint,
    balance_after_cents bigint,
    description text,
    metadata jsonb,
    created_at timestamptz DEFAULT now()
);
"""

CREDITS = 5000
PRICE = Decimal("49.00")


async def seed(pool, user_id, session_id, start_balance=Decimal("100.00")):
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO users (id) VALUES ($1)", user_id)
        await conn.execute(
            "INSERT INTO user_credits (user_id, balance, tier, monthly_cap) VALUES ($1,$2,'professional',$2)",
            user_id, start_balance,
        )
        await conn.execute(
            """
            INSERT INTO credit_purchases
              (user_id, package_name, amount_credits, amount_paid, stripe_checkout_session_id, status, metadata)
            VALUES ($1,'Professional Pack',$2,$3,$4,'pending','{}'::jsonb)
            """,
            user_id, Decimal(CREDITS), PRICE, session_id,
        )


async def balance(pool, user_id):
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT balance FROM user_credits WHERE user_id=$1", user_id)


async def status_of(pool, session_id):
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT status FROM credit_purchases WHERE stripe_checkout_session_id=$1", session_id)


async def main():
    pool = await asyncpg.create_pool(DSN, min_size=2, max_size=10)
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA)

    start = Decimal("100.00")
    expected_after = start + Decimal(CREDITS)

    # -- TEST 1: single delivery grants exactly the purchased amount ------------------
    print("TEST 1: single delivery")
    u1, s1 = uuid.uuid4(), "cs_test_single"
    await seed(pool, u1, s1, start)
    r = await process_credit_webhook(pool, s1, str(u1), CREDITS, "professional", "pi_1")
    check("single: returns success", r["status"] == "success", r)
    check("single: balance += exactly credits", await balance(pool, u1) == expected_after,
          f"{await balance(pool, u1)} == {expected_after}")
    check("single: status='completed'", await status_of(pool, s1) == "completed")

    # -- TEST 2: duplicate delivery must NOT double-grant -----------------------------
    print("TEST 2: duplicate (redelivered) event")
    r2 = await process_credit_webhook(pool, s1, str(u1), CREDITS, "professional", "pi_1")
    check("dup: returns already_processed", r2["status"] == "already_processed", r2)
    check("dup: balance UNCHANGED (no double-grant)", await balance(pool, u1) == expected_after,
          f"{await balance(pool, u1)} == {expected_after}")

    # -- TEST 3: N concurrent duplicate deliveries race -> grant exactly once ---------
    print("TEST 3: 6 concurrent duplicate deliveries")
    u3, s3 = uuid.uuid4(), "cs_test_concurrent"
    await seed(pool, u3, s3, start)
    results = await asyncio.gather(*[
        process_credit_webhook(pool, s3, str(u3), CREDITS, "professional", "pi_3")
        for _ in range(6)
    ])
    n_success = sum(1 for x in results if x["status"] == "success")
    check("concurrent: exactly ONE delivery granted", n_success == 1, f"n_success={n_success}")
    check("concurrent: balance += credits ONCE", await balance(pool, u3) == expected_after,
          f"{await balance(pool, u3)} == {expected_after}")
    # transaction log should show exactly one allocation row for this user
    async with pool.acquire() as conn:
        n_alloc = await conn.fetchval(
            "SELECT count(*) FROM transactions WHERE user_id=$1 AND type='allocation'", u3)
    check("concurrent: exactly ONE allocation ledger row", n_alloc == 1, f"n_alloc={n_alloc}")

    # -- TEST 4: failure mid-grant rolls back, retry succeeds exactly once ------------
    print("TEST 4: crash between grant and status-flip -> rollback, then retry")
    u4, s4 = uuid.uuid4(), "cs_test_failretry"
    await seed(pool, u4, s4, start)
    try:
        await process_credit_webhook(pool, s4, str(u4), CREDITS, "professional", "pi_4",
                                     fail_after_grant=True)
        raised = False
    except InjectedFailure:
        raised = True
    check("fail: exception propagated (would 500 -> Stripe retries)", raised)
    check("fail: balance rolled back to start (no orphan credits)", await balance(pool, u4) == start,
          f"{await balance(pool, u4)} == {start}")
    check("fail: status NOT left 'completed'", await status_of(pool, s4) == "pending",
          await status_of(pool, s4))
    # the retry (no injected failure) must succeed exactly once
    r4 = await process_credit_webhook(pool, s4, str(u4), CREDITS, "professional", "pi_4")
    check("fail-retry: succeeds", r4["status"] == "success", r4)
    check("fail-retry: balance += credits exactly once", await balance(pool, u4) == expected_after,
          f"{await balance(pool, u4)} == {expected_after}")
    check("fail-retry: status='completed'", await status_of(pool, s4) == "completed")
    # and a duplicate AFTER the successful retry still no-ops
    r4b = await process_credit_webhook(pool, s4, str(u4), CREDITS, "professional", "pi_4")
    check("fail-retry: later duplicate no-ops", r4b["status"] == "already_processed"
          and await balance(pool, u4) == expected_after)

    # -- TEST 5: unknown session acked with 200, no grant -----------------------------
    print("TEST 5: unknown checkout session")
    r5 = await process_credit_webhook(pool, "cs_never_seen", str(uuid.uuid4()), CREDITS,
                                      "professional", "pi_5")
    check("unknown: acked as ignored (no 500 retry storm)", r5["status"] == "ignored", r5)

    await pool.close()

    print()
    if FAIL:
        print(f"RESULT: FAIL ({len(FAIL)} assertion(s) failed): {FAIL}")
        return 1
    print("RESULT: PASS - all idempotency / exactly-once assertions held")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
