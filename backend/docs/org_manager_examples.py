"""
Organization Manager - Usage Examples
Demonstrates common patterns and use cases
"""

from org_manager import org_manager

# ==================== Example 1: Creating Organizations ====================

def example_create_organization():
    """Create a new organization"""
    print("\n=== Example 1: Creating Organization ===")

    # Create basic organization
    org_id = org_manager.create_organization("Acme Corporation")
    print(f"Created organization: {org_id}")

    # Create organization with custom plan
    org_id_pro = org_manager.create_organization(
        "Pro Tech Inc",
        plan_tier="professional"
    )
    print(f"Created professional org: {org_id_pro}")

    return org_id, org_id_pro


# ==================== Example 2: Adding Users ====================

def example_add_users(org_id):
    """Add users to an organization"""
    print("\n=== Example 2: Adding Users ===")

    # Add owner
    org_manager.add_user_to_org(org_id, "user_alice", role="owner")
    print("Added Alice as owner")

    # Add members
    org_manager.add_user_to_org(org_id, "user_bob", role="member")
    org_manager.add_user_to_org(org_id, "user_charlie", role="member")
    print("Added Bob and Charlie as members")

    # Add billing admin
    org_manager.add_user_to_org(org_id, "user_diana", role="billing_admin")
    print("Added Diana as billing admin")

    # List all users
    users = org_manager.get_org_users(org_id)
    print(f"\nTotal users in org: {len(users)}")
    for user in users:
        print(f"  - {user.user_id}: {user.role}")


# ==================== Example 3: Managing User Roles ====================

def example_manage_roles(org_id):
    """Update user roles"""
    print("\n=== Example 3: Managing Roles ===")

    # Check current role
    role = org_manager.get_user_role_in_org(org_id, "user_bob")
    print(f"Bob's current role: {role}")

    # Promote Bob to billing admin
    org_manager.update_user_role(org_id, "user_bob", "billing_admin")
    print("Promoted Bob to billing_admin")

    # Verify change
    new_role = org_manager.get_user_role_in_org(org_id, "user_bob")
    print(f"Bob's new role: {new_role}")


# ==================== Example 4: Billing Integration ====================

def example_billing_integration(org_id):
    """Integrate with billing systems"""
    print("\n=== Example 4: Billing Integration ===")

    # Organization just signed up and you created them in Lago and Stripe
    lago_customer_id = "lago_cust_abc123xyz"
    stripe_customer_id = "cus_StripeABC123"

    org_manager.update_org_billing_ids(
        org_id,
        lago_id=lago_customer_id,
        stripe_id=stripe_customer_id
    )
    print(f"Updated billing IDs for {org_id}")

    # Retrieve organization and verify
    org = org_manager.get_org(org_id)
    print(f"Organization: {org.name}")
    print(f"  Lago Customer ID: {org.lago_customer_id}")
    print(f"  Stripe Customer ID: {org.stripe_customer_id}")


# ==================== Example 5: Plan Upgrades ====================

def example_plan_upgrade(org_id):
    """Handle plan upgrades"""
    print("\n=== Example 5: Plan Upgrade ===")

    org = org_manager.get_org(org_id)
    print(f"Current plan: {org.plan_tier}")

    # Customer upgrades to professional
    org_manager.update_org_plan(org_id, "professional")
    print("Upgraded to professional plan")

    # Verify upgrade
    org = org_manager.get_org(org_id)
    print(f"New plan: {org.plan_tier}")


# ==================== Example 6: User's Organizations ====================

def example_user_organizations():
    """Get all organizations for a user"""
    print("\n=== Example 6: User's Organizations ===")

    # Create multiple organizations and add same user
    org1 = org_manager.create_organization("Company A")
    org2 = org_manager.create_organization("Company B")
    org3 = org_manager.create_organization("Company C")

    user_id = "user_freelancer"

    org_manager.add_user_to_org(org1, user_id, role="member")
    org_manager.add_user_to_org(org2, user_id, role="owner")
    org_manager.add_user_to_org(org3, user_id, role="billing_admin")

    # Get all orgs for this user
    user_orgs = org_manager.get_user_orgs(user_id)
    print(f"\n{user_id} is in {len(user_orgs)} organizations:")

    for org in user_orgs:
        role = org_manager.get_user_role_in_org(org.id, user_id)
        print(f"  - {org.name} ({org.plan_tier}) - Role: {role}")


# ==================== Example 7: Searching & Filtering ====================

def example_search_and_filter():
    """Search and filter organizations"""
    print("\n=== Example 7: Searching & Filtering ===")

    # Create some test orgs
    org_manager.create_organization("Tech Startup Inc", plan_tier="starter")
    org_manager.create_organization("Tech Solutions LLC", plan_tier="professional")
    org_manager.create_organization("Global Enterprises", plan_tier="enterprise")

    # Search by name
    tech_orgs = org_manager.search_organizations("tech")
    print(f"\nOrganizations with 'tech' in name: {len(tech_orgs)}")
    for org in tech_orgs:
        print(f"  - {org.name}")

    # Filter by plan
    pro_orgs = org_manager.get_organizations_by_plan("professional")
    print(f"\nProfessional plan organizations: {len(pro_orgs)}")
    for org in pro_orgs:
        print(f"  - {org.name}")

    # List all organizations
    all_orgs = org_manager.list_all_organizations()
    print(f"\nTotal organizations: {len(all_orgs)}")


# ==================== Example 8: Organization Lifecycle ====================

def example_organization_lifecycle():
    """Demonstrate full organization lifecycle"""
    print("\n=== Example 8: Organization Lifecycle ===")

    # 1. Create organization
    org_id = org_manager.create_organization("Lifecycle Demo Corp")
    print(f"1. Created: {org_id}")

    # 2. Add initial owner
    org_manager.add_user_to_org(org_id, "user_founder", role="owner")
    print("2. Added founder as owner")

    # 3. Connect billing systems
    org_manager.update_org_billing_ids(
        org_id,
        lago_id="lago_lifecycle_demo",
        stripe_id="cus_lifecycle_demo"
    )
    print("3. Connected billing systems")

    # 4. Add team members
    org_manager.add_user_to_org(org_id, "user_dev1", role="member")
    org_manager.add_user_to_org(org_id, "user_dev2", role="member")
    print("4. Added team members")

    # 5. Upgrade plan
    org_manager.update_org_plan(org_id, "enterprise")
    print("5. Upgraded to enterprise")

    # 6. Add billing admin
    org_manager.add_user_to_org(org_id, "user_cfo", role="billing_admin")
    print("6. Added CFO as billing admin")

    # 7. Display final state
    org = org_manager.get_org(org_id)
    users = org_manager.get_org_users(org_id)

    print(f"\nFinal State:")
    print(f"  Organization: {org.name}")
    print(f"  Status: {org.status}")
    print(f"  Plan: {org.plan_tier}")
    print(f"  Team Size: {len(users)}")
    print(f"  Lago ID: {org.lago_customer_id}")
    print(f"  Stripe ID: {org.stripe_customer_id}")


# ==================== Example 9: Error Handling ====================

def example_error_handling():
    """Demonstrate proper error handling"""
    print("\n=== Example 9: Error Handling ===")

    # Example 1: Duplicate organization name
    try:
        org_manager.create_organization("Duplicate Test")
        org_manager.create_organization("Duplicate Test")  # This will fail
    except ValueError as e:
        print(f"Caught expected error: {e}")

    # Example 2: Invalid role
    org_id = org_manager.create_organization("Error Handling Corp")
    try:
        org_manager.add_user_to_org(org_id, "user_test", role="invalid_role")
    except ValueError as e:
        print(f"Caught expected error: {e}")

    # Example 3: Non-existent organization
    result = org_manager.update_org_plan("org_nonexistent", "professional")
    print(f"Update non-existent org result: {result}")  # Returns False

    # Example 4: Duplicate user in org
    org_manager.add_user_to_org(org_id, "user_test", role="member")
    try:
        org_manager.add_user_to_org(org_id, "user_test", role="owner")
    except ValueError as e:
        print(f"Caught expected error: {e}")


# ==================== Example 10: Multi-Organization User Workflow ====================

def example_multi_org_workflow():
    """Realistic workflow for user in multiple organizations"""
    print("\n=== Example 10: Multi-Organization Workflow ===")

    user_id = "user_consultant"

    # User is a consultant working for multiple clients
    client1 = org_manager.create_organization("Client Alpha Corp")
    client2 = org_manager.create_organization("Client Beta LLC")
    client3 = org_manager.create_organization("Client Gamma Inc")

    # Add as member to each client
    org_manager.add_user_to_org(client1, user_id, role="member")
    org_manager.add_user_to_org(client2, user_id, role="owner")  # Owns this one
    org_manager.add_user_to_org(client3, user_id, role="member")

    # User logs in and needs to see all their organizations
    user_orgs = org_manager.get_user_orgs(user_id)

    print(f"\n{user_id}'s Dashboard:")
    print(f"Member of {len(user_orgs)} organizations:\n")

    for org in user_orgs:
        role = org_manager.get_user_role_in_org(org.id, user_id)
        users_count = len(org_manager.get_org_users(org.id))

        print(f"  {org.name}")
        print(f"    Plan: {org.plan_tier}")
        print(f"    Your Role: {role}")
        print(f"    Team Size: {users_count}")
        print(f"    Status: {org.status}")
        print()


# ==================== Run All Examples ====================

def run_all_examples():
    """Run all examples"""
    print("=" * 60)
    print("Organization Manager - Complete Examples")
    print("=" * 60)

    # Run examples
    org_id, org_id_pro = example_create_organization()
    example_add_users(org_id)
    example_manage_roles(org_id)
    example_billing_integration(org_id)
    example_plan_upgrade(org_id)
    example_user_organizations()
    example_search_and_filter()
    example_organization_lifecycle()
    example_error_handling()
    example_multi_org_workflow()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
