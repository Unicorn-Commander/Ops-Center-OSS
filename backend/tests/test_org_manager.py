"""
Test suite for Organization Manager
Tests all CRUD operations, user management, and thread safety
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
import threading
import time

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from org_manager import OrgManager, Organization, OrgUser


class TestOrgManager:
    """Test suite for OrgManager class"""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def org_mgr(self, temp_data_dir):
        """Create OrgManager instance with temp directory"""
        return OrgManager(data_dir=temp_data_dir)

    # ==================== Organization CRUD Tests ====================

    def test_create_organization(self, org_mgr):
        """Test creating a new organization"""
        org_id = org_mgr.create_organization("Test Corp")

        assert org_id.startswith("org_")

        org = org_mgr.get_org(org_id)
        assert org is not None
        assert org.name == "Test Corp"
        assert org.plan_tier == "founders_friend"
        assert org.status == "active"

    def test_create_organization_with_custom_plan(self, org_mgr):
        """Test creating organization with custom plan tier"""
        org_id = org_mgr.create_organization("Premium Corp", plan_tier="professional")

        org = org_mgr.get_org(org_id)
        assert org.plan_tier == "professional"

    def test_create_duplicate_organization(self, org_mgr):
        """Test that duplicate organization names are rejected"""
        org_mgr.create_organization("Unique Corp")

        with pytest.raises(ValueError, match="already exists"):
            org_mgr.create_organization("Unique Corp")

    def test_create_organization_empty_name(self, org_mgr):
        """Test that empty names are rejected"""
        with pytest.raises(ValueError, match="cannot be empty"):
            org_mgr.create_organization("")

    def test_get_nonexistent_organization(self, org_mgr):
        """Test getting organization that doesn't exist"""
        org = org_mgr.get_org("org_nonexistent")
        assert org is None

    def test_update_org_billing_ids(self, org_mgr):
        """Test updating organization billing IDs"""
        org_id = org_mgr.create_organization("Billing Test Corp")

        success = org_mgr.update_org_billing_ids(
            org_id,
            lago_id="lago_123",
            stripe_id="cus_456"
        )

        assert success is True

        org = org_mgr.get_org(org_id)
        assert org.lago_customer_id == "lago_123"
        assert org.stripe_customer_id == "cus_456"

    def test_update_billing_ids_partial(self, org_mgr):
        """Test updating only one billing ID"""
        org_id = org_mgr.create_organization("Partial Update Corp")

        org_mgr.update_org_billing_ids(org_id, lago_id="lago_abc")
        org = org_mgr.get_org(org_id)
        assert org.lago_customer_id == "lago_abc"
        assert org.stripe_customer_id is None

        org_mgr.update_org_billing_ids(org_id, stripe_id="cus_xyz")
        org = org_mgr.get_org(org_id)
        assert org.lago_customer_id == "lago_abc"
        assert org.stripe_customer_id == "cus_xyz"

    def test_update_org_plan(self, org_mgr):
        """Test updating organization plan tier"""
        org_id = org_mgr.create_organization("Plan Test Corp")

        success = org_mgr.update_org_plan(org_id, "enterprise")
        assert success is True

        org = org_mgr.get_org(org_id)
        assert org.plan_tier == "enterprise"

    def test_update_org_status(self, org_mgr):
        """Test updating organization status"""
        org_id = org_mgr.create_organization("Status Test Corp")

        success = org_mgr.update_org_status(org_id, "suspended")
        assert success is True

        org = org_mgr.get_org(org_id)
        assert org.status == "suspended"

    # ==================== User Management Tests ====================

    def test_add_user_to_org(self, org_mgr):
        """Test adding a user to an organization"""
        org_id = org_mgr.create_organization("User Test Corp")

        success = org_mgr.add_user_to_org(org_id, "user_123", role="owner")
        assert success is True

        users = org_mgr.get_org_users(org_id)
        assert len(users) == 1
        assert users[0].user_id == "user_123"
        assert users[0].role == "owner"

    def test_add_multiple_users(self, org_mgr):
        """Test adding multiple users to an organization"""
        org_id = org_mgr.create_organization("Multi User Corp")

        org_mgr.add_user_to_org(org_id, "user_1", role="owner")
        org_mgr.add_user_to_org(org_id, "user_2", role="member")
        org_mgr.add_user_to_org(org_id, "user_3", role="billing_admin")

        users = org_mgr.get_org_users(org_id)
        assert len(users) == 3

        user_ids = {u.user_id for u in users}
        assert user_ids == {"user_1", "user_2", "user_3"}

    def test_add_duplicate_user(self, org_mgr):
        """Test that adding same user twice fails"""
        org_id = org_mgr.create_organization("Duplicate User Corp")

        org_mgr.add_user_to_org(org_id, "user_123", role="member")

        with pytest.raises(ValueError, match="already in organization"):
            org_mgr.add_user_to_org(org_id, "user_123", role="owner")

    def test_add_user_invalid_role(self, org_mgr):
        """Test that invalid roles are rejected"""
        org_id = org_mgr.create_organization("Invalid Role Corp")

        with pytest.raises(ValueError, match="must be one of"):
            org_mgr.add_user_to_org(org_id, "user_123", role="invalid_role")

    def test_remove_user_from_org(self, org_mgr):
        """Test removing a user from an organization"""
        org_id = org_mgr.create_organization("Remove User Corp")
        org_mgr.add_user_to_org(org_id, "user_123", role="member")

        success = org_mgr.remove_user_from_org(org_id, "user_123")
        assert success is True

        users = org_mgr.get_org_users(org_id)
        assert len(users) == 0

    def test_update_user_role(self, org_mgr):
        """Test updating a user's role"""
        org_id = org_mgr.create_organization("Role Update Corp")
        org_mgr.add_user_to_org(org_id, "user_123", role="member")

        success = org_mgr.update_user_role(org_id, "user_123", "owner")
        assert success is True

        role = org_mgr.get_user_role_in_org(org_id, "user_123")
        assert role == "owner"

    def test_get_user_orgs(self, org_mgr):
        """Test getting all organizations for a user"""
        org_id_1 = org_mgr.create_organization("Corp 1")
        org_id_2 = org_mgr.create_organization("Corp 2")
        org_id_3 = org_mgr.create_organization("Corp 3")

        org_mgr.add_user_to_org(org_id_1, "user_123", role="owner")
        org_mgr.add_user_to_org(org_id_2, "user_123", role="member")
        # user_123 is not in org_id_3

        orgs = org_mgr.get_user_orgs("user_123")
        assert len(orgs) == 2

        org_ids = {org.id for org in orgs}
        assert org_ids == {org_id_1, org_id_2}

    def test_get_user_role_in_org(self, org_mgr):
        """Test getting user's role in specific org"""
        org_id = org_mgr.create_organization("Role Check Corp")
        org_mgr.add_user_to_org(org_id, "user_123", role="billing_admin")

        role = org_mgr.get_user_role_in_org(org_id, "user_123")
        assert role == "billing_admin"

        # Non-existent user
        role = org_mgr.get_user_role_in_org(org_id, "user_999")
        assert role is None

    # ==================== Query Tests ====================

    def test_list_all_organizations(self, org_mgr):
        """Test listing all organizations"""
        org_mgr.create_organization("Corp A")
        org_mgr.create_organization("Corp B")
        org_mgr.create_organization("Corp C")

        orgs = org_mgr.list_all_organizations()
        assert len(orgs) == 3

    def test_search_organizations(self, org_mgr):
        """Test searching organizations by name"""
        org_mgr.create_organization("Acme Corp")
        org_mgr.create_organization("Acme Industries")
        org_mgr.create_organization("Beta Corp")

        results = org_mgr.search_organizations("acme")
        assert len(results) == 2

        results = org_mgr.search_organizations("beta")
        assert len(results) == 1

    def test_get_organizations_by_plan(self, org_mgr):
        """Test filtering organizations by plan tier"""
        org_mgr.create_organization("Free Corp", plan_tier="founders_friend")
        org_mgr.create_organization("Pro Corp", plan_tier="professional")
        org_mgr.create_organization("Enterprise Corp", plan_tier="enterprise")
        org_mgr.create_organization("Another Pro Corp", plan_tier="professional")

        pro_orgs = org_mgr.get_organizations_by_plan("professional")
        assert len(pro_orgs) == 2

    # ==================== Thread Safety Tests ====================

    def test_concurrent_organization_creation(self, org_mgr):
        """Test creating organizations concurrently"""
        results = []
        errors = []

        def create_org(index):
            try:
                org_id = org_mgr.create_organization(f"Concurrent Corp {index}")
                results.append(org_id)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_org, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert len(results) == 10
        assert len(set(results)) == 10  # All unique IDs

    def test_concurrent_user_addition(self, org_mgr):
        """Test adding users concurrently"""
        org_id = org_mgr.create_organization("Concurrent Users Corp")
        results = []
        errors = []

        def add_user(index):
            try:
                success = org_mgr.add_user_to_org(
                    org_id,
                    f"user_{index}",
                    role="member"
                )
                results.append(success)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(10):
            thread = threading.Thread(target=add_user, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert all(results)  # All successful

        users = org_mgr.get_org_users(org_id)
        assert len(users) == 10

    # ==================== Data Persistence Tests ====================

    def test_data_persistence(self, temp_data_dir):
        """Test that data persists across manager instances"""
        # Create first manager and add data
        mgr1 = OrgManager(data_dir=temp_data_dir)
        org_id = mgr1.create_organization("Persistent Corp")
        mgr1.add_user_to_org(org_id, "user_123", role="owner")

        # Create new manager instance (simulating restart)
        mgr2 = OrgManager(data_dir=temp_data_dir)

        # Verify data is still there
        org = mgr2.get_org(org_id)
        assert org is not None
        assert org.name == "Persistent Corp"

        users = mgr2.get_org_users(org_id)
        assert len(users) == 1
        assert users[0].user_id == "user_123"

    # ==================== Edge Cases ====================

    def test_get_org_users_empty_org(self, org_mgr):
        """Test getting users from organization with no users"""
        org_id = org_mgr.create_organization("Empty Corp")
        users = org_mgr.get_org_users(org_id)
        assert users == []

    def test_get_user_orgs_no_orgs(self, org_mgr):
        """Test getting orgs for user not in any org"""
        orgs = org_mgr.get_user_orgs("user_orphan")
        assert orgs == []

    def test_operations_on_nonexistent_org(self, org_mgr):
        """Test operations on non-existent organization"""
        fake_org_id = "org_fake123"

        assert org_mgr.update_org_billing_ids(fake_org_id, lago_id="test") is False
        assert org_mgr.update_org_plan(fake_org_id, "professional") is False
        assert org_mgr.update_org_status(fake_org_id, "suspended") is False
        assert org_mgr.add_user_to_org(fake_org_id, "user_123") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
