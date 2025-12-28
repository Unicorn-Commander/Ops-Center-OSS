#!/usr/bin/env python3
"""
Webhook Simulator for Testing
Simulates Stripe and Lago webhooks for testing billing system

Usage:
    # Simulate subscription creation
    python3 simulate_webhooks.py --type lago_subscription_created --email test@example.com

    # Simulate subscription cancellation
    python3 simulate_webhooks.py --type lago_subscription_cancelled --email test@example.com

    # Simulate invoice payment
    python3 simulate_webhooks.py --type stripe_invoice_paid --customer cus_123

    # Run all webhook scenarios
    python3 simulate_webhooks.py --run-all
"""

import asyncio
import httpx
import argparse
import json
import os
import sys
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Optional

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8084")
LAGO_WEBHOOK_SECRET = os.getenv("LAGO_WEBHOOK_SECRET", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")


def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")


def print_info(msg):
    print(f"{BLUE}ℹ {msg}{RESET}")


def print_section(title):
    print(f"\n{BLUE}{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}{RESET}\n")


def generate_lago_signature(payload: str, secret: str) -> str:
    """Generate Lago webhook signature"""
    if not secret:
        return ""
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def generate_stripe_signature(payload: str, secret: str) -> str:
    """Generate Stripe webhook signature"""
    if not secret:
        return ""
    timestamp = str(int(datetime.now().timestamp()))
    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


class WebhookSimulator:
    """Simulate webhook events for testing"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0, verify=False)

    async def close(self):
        await self.client.aclose()

    async def send_lago_webhook(
        self,
        payload: Dict,
        sign: bool = True
    ) -> httpx.Response:
        """Send Lago webhook to server"""
        payload_str = json.dumps(payload)
        headers = {"Content-Type": "application/json"}

        if sign and LAGO_WEBHOOK_SECRET:
            signature = generate_lago_signature(payload_str, LAGO_WEBHOOK_SECRET)
            headers["X-Lago-Signature"] = signature

        response = await self.client.post(
            f"{self.base_url}/api/v1/webhooks/lago",
            content=payload_str,
            headers=headers
        )

        return response

    async def send_stripe_webhook(
        self,
        payload: Dict,
        sign: bool = True
    ) -> httpx.Response:
        """Send Stripe webhook to server"""
        payload_str = json.dumps(payload)
        headers = {"Content-Type": "application/json"}

        if sign and STRIPE_WEBHOOK_SECRET:
            signature = generate_stripe_signature(payload_str, STRIPE_WEBHOOK_SECRET)
            headers["Stripe-Signature"] = signature

        # Note: Stripe webhook endpoint would need to be implemented
        # For now, sending to test endpoint
        response = await self.client.post(
            f"{self.base_url}/api/v1/webhooks/stripe",
            content=payload_str,
            headers=headers
        )

        return response

    async def simulate_lago_subscription_created(
        self,
        email: str,
        plan_code: str = "starter_monthly"
    ):
        """Simulate Lago subscription creation"""
        print_info(f"Simulating Lago subscription creation for {email}")

        payload = {
            "webhook_type": "subscription.created",
            "subscription": {
                "lago_id": f"sub_test_{datetime.now().timestamp()}",
                "plan_code": plan_code,
                "status": "active",
                "started_at": datetime.now().isoformat()
            },
            "customer": {
                "lago_id": f"cus_test_{email}",
                "email": email,
                "name": "Test User"
            }
        }

        response = await self.send_lago_webhook(payload)

        if response.status_code == 200:
            print_success(f"Webhook accepted: {response.status_code}")
            print_info(f"Response: {response.json()}")
        else:
            print_error(f"Webhook failed: {response.status_code}")
            print_error(f"Response: {response.text}")

        return response

    async def simulate_lago_subscription_updated(
        self,
        email: str,
        new_plan_code: str = "professional_monthly"
    ):
        """Simulate Lago subscription update (upgrade/downgrade)"""
        print_info(f"Simulating Lago subscription update for {email}")

        payload = {
            "webhook_type": "subscription.updated",
            "subscription": {
                "lago_id": f"sub_test_{email}",
                "plan_code": new_plan_code,
                "status": "active",
                "updated_at": datetime.now().isoformat()
            },
            "customer": {
                "email": email
            }
        }

        response = await self.send_lago_webhook(payload)

        if response.status_code == 200:
            print_success(f"Webhook accepted: {response.status_code}")
        else:
            print_error(f"Webhook failed: {response.status_code}")

        return response

    async def simulate_lago_subscription_cancelled(self, email: str):
        """Simulate Lago subscription cancellation"""
        print_info(f"Simulating Lago subscription cancellation for {email}")

        payload = {
            "webhook_type": "subscription.cancelled",
            "subscription": {
                "lago_id": f"sub_test_{email}",
                "status": "terminated",
                "terminated_at": datetime.now().isoformat()
            },
            "customer": {
                "email": email
            }
        }

        response = await self.send_lago_webhook(payload)

        if response.status_code == 200:
            print_success(f"Webhook accepted: {response.status_code}")
        else:
            print_error(f"Webhook failed: {response.status_code}")

        return response

    async def simulate_lago_invoice_paid(
        self,
        email: str,
        amount_cents: int = 1900
    ):
        """Simulate successful invoice payment"""
        print_info(f"Simulating invoice payment for {email}")

        payload = {
            "webhook_type": "invoice.paid",
            "invoice": {
                "lago_id": f"inv_test_{datetime.now().timestamp()}",
                "amount_cents": amount_cents,
                "currency": "USD",
                "payment_status": "succeeded",
                "paid_at": datetime.now().isoformat()
            },
            "customer": {
                "email": email
            }
        }

        response = await self.send_lago_webhook(payload)

        if response.status_code == 200:
            print_success(f"Webhook accepted: {response.status_code}")
        else:
            print_error(f"Webhook failed: {response.status_code}")

        return response

    async def run_all_scenarios(self, test_email: str = "test@example.com"):
        """Run all webhook scenarios"""
        print_section("WEBHOOK SIMULATION - ALL SCENARIOS")

        scenarios = [
            ("Subscription Created", self.simulate_lago_subscription_created(test_email)),
            ("Subscription Updated", self.simulate_lago_subscription_updated(test_email)),
            ("Invoice Paid", self.simulate_lago_invoice_paid(test_email)),
            ("Subscription Cancelled", self.simulate_lago_subscription_cancelled(test_email))
        ]

        results = []
        for name, coro in scenarios:
            print_section(name)
            try:
                response = await coro
                results.append((name, response.status_code == 200))
                await asyncio.sleep(0.5)  # Brief pause between scenarios
            except Exception as e:
                print_error(f"Scenario failed: {e}")
                results.append((name, False))

        # Summary
        print_section("SIMULATION SUMMARY")
        passed = sum(1 for _, success in results if success)
        total = len(results)

        print_info(f"Scenarios: {passed}/{total} successful")

        for name, success in results:
            if success:
                print_success(name)
            else:
                print_error(name)


async def main():
    parser = argparse.ArgumentParser(
        description="Webhook Simulator for UC-1 Pro Billing System"
    )
    parser.add_argument(
        "--type",
        choices=[
            "lago_subscription_created",
            "lago_subscription_updated",
            "lago_subscription_cancelled",
            "lago_invoice_paid"
        ],
        help="Type of webhook to simulate"
    )
    parser.add_argument(
        "--email",
        default="test@example.com",
        help="Customer email address"
    )
    parser.add_argument(
        "--plan",
        default="starter_monthly",
        help="Plan code (for subscription webhooks)"
    )
    parser.add_argument(
        "--amount",
        type=int,
        default=1900,
        help="Invoice amount in cents"
    )
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run all webhook scenarios"
    )
    parser.add_argument(
        "--base-url",
        default=BASE_URL,
        help=f"Base URL (default: {BASE_URL})"
    )

    args = parser.parse_args()

    print_section("WEBHOOK SIMULATOR")
    print_info(f"Target URL: {args.base_url}")
    print_info(f"Lago Secret Configured: {'Yes' if LAGO_WEBHOOK_SECRET else 'No'}")
    print_info(f"Timestamp: {datetime.now().isoformat()}")

    simulator = WebhookSimulator(args.base_url)

    try:
        if args.run_all:
            await simulator.run_all_scenarios(args.email)
        elif args.type:
            if args.type == "lago_subscription_created":
                await simulator.simulate_lago_subscription_created(args.email, args.plan)
            elif args.type == "lago_subscription_updated":
                await simulator.simulate_lago_subscription_updated(args.email, args.plan)
            elif args.type == "lago_subscription_cancelled":
                await simulator.simulate_lago_subscription_cancelled(args.email)
            elif args.type == "lago_invoice_paid":
                await simulator.simulate_lago_invoice_paid(args.email, args.amount)
        else:
            parser.print_help()

    except Exception as e:
        print_error(f"Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await simulator.close()

    print_section("COMPLETE")
    print_success("Simulation completed")


if __name__ == "__main__":
    asyncio.run(main())
