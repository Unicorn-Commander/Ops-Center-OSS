#!/usr/bin/env python3
"""
Migration Script: User-Based to Org-Based Billing
Migrates existing Lago customers from user_id to org_id
"""

import asyncio
import sys
import os
import logging
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lago_integration import (
    get_customer,
    create_org_customer,
    migrate_user_to_org,
    is_org_customer,
    LagoIntegrationError
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# Migration Mapping
# ============================================

async def get_user_to_org_mapping() -> List[Dict[str, Any]]:
    """
    Get mapping of user_id to org_id from your database.
    CUSTOMIZE THIS FUNCTION based on your database schema.

    Returns:
        List of mappings: [
            {
                "user_id": "user_123",
                "org_id": "org_456",
                "org_name": "ACME Corp",
                "email": "billing@acme.com"
            },
            ...
        ]
    """
    # TODO: Replace with your actual database query
    # Example:
    # from keycloak_integration import get_all_users
    # users = await get_all_users()
    # mappings = []
    # for user in users:
    #     org_id = user.get("attributes", {}).get("org_id", [None])[0]
    #     if org_id:
    #         mappings.append({
    #             "user_id": user["id"],
    #             "org_id": org_id,
    #             "org_name": user.get("attributes", {}).get("org_name", [user["username"]])[0],
    #             "email": user["email"]
    #         })
    # return mappings

    # Placeholder - replace with real data
    logger.warning("Using placeholder mapping data. Update get_user_to_org_mapping() with real database query.")
    return []


# ============================================
# Migration Functions
# ============================================

async def check_migration_status(mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check current migration status.
    Returns stats on how many users are already migrated.
    """
    stats = {
        "total_users": len(mappings),
        "already_org_customers": 0,
        "user_customers": 0,
        "no_customer": 0,
        "needs_migration": []
    }

    for mapping in mappings:
        user_id = mapping["user_id"]
        org_id = mapping["org_id"]

        # Check if org customer exists
        org_customer = await get_customer(org_id)
        if org_customer:
            stats["already_org_customers"] += 1
            continue

        # Check if user customer exists
        user_customer = await get_customer(user_id)
        if user_customer:
            stats["user_customers"] += 1
            stats["needs_migration"].append(mapping)
        else:
            stats["no_customer"] += 1

    return stats


async def migrate_single_customer(mapping: Dict[str, Any], dry_run: bool = True) -> bool:
    """
    Migrate a single customer from user_id to org_id.

    Args:
        mapping: User to org mapping
        dry_run: If True, only log what would be done

    Returns:
        True if successful, False otherwise
    """
    user_id = mapping["user_id"]
    org_id = mapping["org_id"]
    org_name = mapping["org_name"]
    email = mapping["email"]

    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Migrating customer:")
    logger.info(f"  User ID: {user_id}")
    logger.info(f"  Org ID: {org_id}")
    logger.info(f"  Org Name: {org_name}")
    logger.info(f"  Email: {email}")

    if dry_run:
        logger.info(f"  Would create org customer and link to user {user_id}")
        return True

    try:
        success = await migrate_user_to_org(user_id, org_id, org_name, email)
        if success:
            logger.info(f"✓ Successfully migrated {user_id} -> {org_id}")
        else:
            logger.error(f"✗ Failed to migrate {user_id} -> {org_id}")
        return success

    except Exception as e:
        logger.error(f"✗ Error migrating {user_id} -> {org_id}: {e}")
        return False


async def migrate_all_customers(mappings: List[Dict[str, Any]], dry_run: bool = True):
    """
    Migrate all customers from user-based to org-based billing.

    Args:
        mappings: List of user to org mappings
        dry_run: If True, only simulate migration
    """
    logger.info("=" * 60)
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Starting Lago billing migration")
    logger.info(f"Total mappings to process: {len(mappings)}")
    logger.info("=" * 60)

    # Check current status
    logger.info("\nChecking current migration status...")
    stats = await check_migration_status(mappings)

    logger.info("\nCurrent Status:")
    logger.info(f"  Total users: {stats['total_users']}")
    logger.info(f"  Already org customers: {stats['already_org_customers']}")
    logger.info(f"  User customers (need migration): {stats['user_customers']}")
    logger.info(f"  No Lago customer: {stats['no_customer']}")

    if not stats["needs_migration"]:
        logger.info("\n✓ No migration needed! All customers are already org-based.")
        return

    # Confirm migration
    if not dry_run:
        logger.info(f"\n⚠️  About to migrate {len(stats['needs_migration'])} customers")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Migration cancelled.")
            return

    # Perform migration
    logger.info(f"\n{'Simulating' if dry_run else 'Performing'} migration...")
    results = {
        "success": 0,
        "failed": 0,
        "errors": []
    }

    for i, mapping in enumerate(stats["needs_migration"], 1):
        logger.info(f"\n[{i}/{len(stats['needs_migration'])}] Processing...")

        success = await migrate_single_customer(mapping, dry_run)

        if success:
            results["success"] += 1
        else:
            results["failed"] += 1
            results["errors"].append({
                "user_id": mapping["user_id"],
                "org_id": mapping["org_id"]
            })

        # Add small delay to avoid rate limiting
        await asyncio.sleep(0.5)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Migration Summary")
    logger.info("=" * 60)
    logger.info(f"Total processed: {len(stats['needs_migration'])}")
    logger.info(f"Successful: {results['success']}")
    logger.info(f"Failed: {results['failed']}")

    if results["errors"]:
        logger.error("\nFailed migrations:")
        for error in results["errors"]:
            logger.error(f"  {error['user_id']} -> {error['org_id']}")

    if dry_run:
        logger.info("\n⚠️  This was a DRY RUN. No changes were made.")
        logger.info("Run with --execute to perform actual migration.")


# ============================================
# Verification
# ============================================

async def verify_migration(mappings: List[Dict[str, Any]]):
    """
    Verify that migration was successful.
    Checks that all org customers exist in Lago.
    """
    logger.info("\n" + "=" * 60)
    logger.info("Verifying Migration")
    logger.info("=" * 60)

    verification_results = {
        "verified": 0,
        "missing": 0,
        "errors": []
    }

    for mapping in mappings:
        org_id = mapping["org_id"]
        org_name = mapping["org_name"]

        org_customer = await get_customer(org_id)

        if org_customer:
            logger.info(f"✓ Verified: {org_id} ({org_name})")
            verification_results["verified"] += 1
        else:
            logger.error(f"✗ Missing: {org_id} ({org_name})")
            verification_results["missing"] += 1
            verification_results["errors"].append({
                "org_id": org_id,
                "org_name": org_name
            })

    logger.info("\n" + "=" * 60)
    logger.info("Verification Summary")
    logger.info("=" * 60)
    logger.info(f"Total checked: {len(mappings)}")
    logger.info(f"Verified: {verification_results['verified']}")
    logger.info(f"Missing: {verification_results['missing']}")

    if verification_results["errors"]:
        logger.error("\nMissing org customers:")
        for error in verification_results["errors"]:
            logger.error(f"  {error['org_id']} ({error['org_name']})")

    return verification_results["missing"] == 0


# ============================================
# Main Script
# ============================================

async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate Lago billing from user-based to org-based"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute migration (default is dry-run)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify migration status"
    )
    parser.add_argument(
        "--mapping-file",
        type=str,
        help="JSON file with user-to-org mappings (optional)"
    )

    args = parser.parse_args()

    # Get mappings
    if args.mapping_file:
        import json
        with open(args.mapping_file, 'r') as f:
            mappings = json.load(f)
        logger.info(f"Loaded {len(mappings)} mappings from {args.mapping_file}")
    else:
        mappings = await get_user_to_org_mapping()

    if not mappings:
        logger.error("No user-to-org mappings found!")
        logger.error("Update get_user_to_org_mapping() or provide --mapping-file")
        return 1

    # Verify only
    if args.verify:
        success = await verify_migration(mappings)
        return 0 if success else 1

    # Migrate
    dry_run = not args.execute
    await migrate_all_customers(mappings, dry_run=dry_run)

    # Auto-verify after actual migration
    if args.execute:
        logger.info("\nRunning verification...")
        await verify_migration(mappings)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
