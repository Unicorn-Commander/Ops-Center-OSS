"""
Organization Management Module for UC-Cloud
Handles multi-tenant organization structure with billing integration
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import uuid4
import json
import os
import fcntl
import logging
from contextlib import contextmanager
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Data Models ====================

class Organization(BaseModel):
    """
    Organization model representing a tenant in the system

    Attributes:
        id: Unique organization identifier (org_{uuid4})
        name: Organization name
        created_at: Timestamp of organization creation
        plan_tier: Current subscription plan (defaults to founders_friend)
        lago_customer_id: Lago billing system customer ID
        stripe_customer_id: Stripe payment system customer ID
        status: Organization status (active, suspended, deleted)
    """
    id: str = Field(..., description="Unique organization ID")
    name: str = Field(..., min_length=1, max_length=200, description="Organization name")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    plan_tier: str = Field(default="founders_friend", description="Current subscription plan")
    lago_customer_id: Optional[str] = Field(default=None, description="Lago customer ID")
    stripe_customer_id: Optional[str] = Field(default=None, description="Stripe customer ID")
    status: str = Field(default="active", description="Organization status")

    @validator('id')
    def validate_id(cls, v):
        """Ensure ID follows org_{uuid} format"""
        if not v.startswith('org_'):
            raise ValueError("Organization ID must start with 'org_'")
        return v

    @validator('status')
    def validate_status(cls, v):
        """Validate status is one of allowed values"""
        allowed_statuses = ['active', 'suspended', 'deleted']
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrgUser(BaseModel):
    """
    Organization user membership model

    Attributes:
        org_id: Organization ID this user belongs to
        user_id: User ID (from Keycloak/Authentik)
        role: User's role within the organization
        joined_at: Timestamp when user joined the organization
    """
    org_id: str = Field(..., description="Organization ID")
    user_id: str = Field(..., description="User ID from auth system")
    role: str = Field(..., description="User role in organization")
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('role')
    def validate_role(cls, v):
        """Validate role is one of allowed values"""
        allowed_roles = ['owner', 'member', 'billing_admin']
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==================== File Operations ====================

@contextmanager
def locked_file(file_path: str, mode: str = 'r'):
    """
    Context manager for thread-safe file operations using file locking

    Args:
        file_path: Path to the file
        mode: File open mode ('r', 'w', 'r+', etc.)

    Yields:
        file: Locked file handle

    Example:
        with locked_file('/path/to/file.json', 'r+') as f:
            data = json.load(f)
            # Modify data
            f.seek(0)
            json.dump(data, f)
            f.truncate()
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Create file if it doesn't exist and we're reading
    if 'r' in mode and not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({}, f)

    # Open and lock file
    file_handle = open(file_path, mode)
    try:
        # Acquire exclusive lock (blocks until available)
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
        yield file_handle
    finally:
        # Release lock and close file
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        file_handle.close()


# ==================== Organization Manager ====================

class OrgManager:
    """
    Organization Manager - Handles organization CRUD operations and user membership

    Features:
        - Thread-safe file operations with locking
        - Organization lifecycle management
        - User-organization relationship management
        - Billing system integration (Lago & Stripe)
        - Audit logging for all operations
    """

    def __init__(
        self,
        data_dir: str = "/app/data"  # Container path (was: /opt/ops-center/backend/data)
    ):
        """
        Initialize OrgManager

        Args:
            data_dir: Directory for storing organization data files
        """
        self.data_dir = Path(data_dir)
        self.orgs_file = self.data_dir / "organizations.json"
        self.org_users_file = self.data_dir / "org_users.json"

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize files if they don't exist
        self._initialize_storage()

        logger.info(f"OrgManager initialized with data_dir: {data_dir}")

    def _initialize_storage(self):
        """Initialize storage files if they don't exist"""
        for file_path in [self.orgs_file, self.org_users_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump({}, f)
                logger.info(f"Created storage file: {file_path}")

    def _load_organizations(self) -> Dict[str, Organization]:
        """
        Load all organizations from storage

        Returns:
            Dictionary mapping org_id to Organization objects
        """
        try:
            with locked_file(str(self.orgs_file), 'r') as f:
                data = json.load(f)
                return {
                    org_id: Organization(**org_data)
                    for org_id, org_data in data.items()
                }
        except Exception as e:
            logger.error(f"Error loading organizations: {e}")
            return {}

    def _save_organizations(self, orgs: Dict[str, Organization]):
        """
        Save organizations to storage

        Args:
            orgs: Dictionary of organizations to save
        """
        try:
            with locked_file(str(self.orgs_file), 'w') as f:
                data = {
                    org_id: org.dict()
                    for org_id, org in orgs.items()
                }
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved {len(orgs)} organizations")
        except Exception as e:
            logger.error(f"Error saving organizations: {e}")
            raise

    def _load_org_users(self) -> Dict[str, List[OrgUser]]:
        """
        Load all organization-user relationships

        Returns:
            Dictionary mapping org_id to list of OrgUser objects
        """
        try:
            with locked_file(str(self.org_users_file), 'r') as f:
                data = json.load(f)
                result = {}
                for org_id, users_list in data.items():
                    result[org_id] = [
                        OrgUser(**user_data)
                        for user_data in users_list
                    ]
                return result
        except Exception as e:
            logger.error(f"Error loading org users: {e}")
            return {}

    def _save_org_users(self, org_users: Dict[str, List[OrgUser]]):
        """
        Save organization-user relationships

        Args:
            org_users: Dictionary of org_id to list of OrgUser objects
        """
        try:
            with locked_file(str(self.org_users_file), 'w') as f:
                data = {
                    org_id: [user.dict() for user in users]
                    for org_id, users in org_users.items()
                }
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved org users for {len(org_users)} organizations")
        except Exception as e:
            logger.error(f"Error saving org users: {e}")
            raise

    # ==================== Organization Operations ====================

    def create_organization(self, name: str, plan_tier: str = "founders_friend") -> str:
        """
        Create a new organization

        Args:
            name: Organization name
            plan_tier: Initial subscription plan (defaults to founders_friend)

        Returns:
            org_id: The newly created organization ID

        Raises:
            ValueError: If organization name is invalid or already exists

        Example:
            org_id = org_manager.create_organization("Acme Corp", "professional")
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Organization name cannot be empty")

        # Load existing organizations
        orgs = self._load_organizations()

        # Check for duplicate name
        for org in orgs.values():
            if org.name.lower() == name.lower():
                raise ValueError(f"Organization with name '{name}' already exists")

        # Generate new org ID
        org_id = f"org_{uuid4()}"

        # Create organization object
        new_org = Organization(
            id=org_id,
            name=name.strip(),
            plan_tier=plan_tier,
            created_at=datetime.utcnow(),
            status="active"
        )

        # Save to storage
        orgs[org_id] = new_org
        self._save_organizations(orgs)

        # Initialize empty user list for this org
        org_users = self._load_org_users()
        org_users[org_id] = []
        self._save_org_users(org_users)

        logger.info(f"Created organization: {org_id} - {name}")
        return org_id

    def get_org(self, org_id: str) -> Optional[Organization]:
        """
        Get organization by ID

        Args:
            org_id: Organization ID to retrieve

        Returns:
            Organization object or None if not found

        Example:
            org = org_manager.get_org("org_12345")
            if org:
                print(f"Organization: {org.name}")
        """
        orgs = self._load_organizations()
        return orgs.get(org_id)

    def update_org_billing_ids(
        self,
        org_id: str,
        lago_id: Optional[str] = None,
        stripe_id: Optional[str] = None
    ) -> bool:
        """
        Update organization billing system IDs

        Args:
            org_id: Organization ID to update
            lago_id: Lago customer ID (optional)
            stripe_id: Stripe customer ID (optional)

        Returns:
            True if successful, False if organization not found

        Example:
            success = org_manager.update_org_billing_ids(
                "org_12345",
                lago_id="lago_cust_abc123",
                stripe_id="cus_xyz789"
            )
        """
        orgs = self._load_organizations()

        if org_id not in orgs:
            logger.warning(f"Organization not found: {org_id}")
            return False

        org = orgs[org_id]

        if lago_id is not None:
            org.lago_customer_id = lago_id
            logger.info(f"Updated Lago ID for {org_id}: {lago_id}")

        if stripe_id is not None:
            org.stripe_customer_id = stripe_id
            logger.info(f"Updated Stripe ID for {org_id}: {stripe_id}")

        self._save_organizations(orgs)
        return True

    def update_org_plan(self, org_id: str, plan_tier: str) -> bool:
        """
        Update organization subscription plan

        Args:
            org_id: Organization ID to update
            plan_tier: New subscription plan tier

        Returns:
            True if successful, False if organization not found
        """
        orgs = self._load_organizations()

        if org_id not in orgs:
            logger.warning(f"Organization not found: {org_id}")
            return False

        orgs[org_id].plan_tier = plan_tier
        self._save_organizations(orgs)

        logger.info(f"Updated plan for {org_id} to {plan_tier}")
        return True

    def update_org_status(self, org_id: str, status: str) -> bool:
        """
        Update organization status

        Args:
            org_id: Organization ID to update
            status: New status (active, suspended, deleted)

        Returns:
            True if successful, False if organization not found
        """
        orgs = self._load_organizations()

        if org_id not in orgs:
            logger.warning(f"Organization not found: {org_id}")
            return False

        orgs[org_id].status = status
        self._save_organizations(orgs)

        logger.info(f"Updated status for {org_id} to {status}")
        return True

    # ==================== User-Organization Operations ====================

    def add_user_to_org(self, org_id: str, user_id: str, role: str = "member") -> bool:
        """
        Add a user to an organization

        Args:
            org_id: Organization ID
            user_id: User ID from authentication system
            role: User role (owner, member, billing_admin)

        Returns:
            True if successful, False if organization doesn't exist

        Raises:
            ValueError: If role is invalid or user already in organization

        Example:
            success = org_manager.add_user_to_org(
                "org_12345",
                "user_abc",
                role="owner"
            )
        """
        # Verify organization exists
        orgs = self._load_organizations()
        if org_id not in orgs:
            logger.warning(f"Organization not found: {org_id}")
            return False

        # Load org users
        org_users = self._load_org_users()

        # Initialize list if org doesn't have users yet
        if org_id not in org_users:
            org_users[org_id] = []

        # Check if user already in organization
        for existing_user in org_users[org_id]:
            if existing_user.user_id == user_id:
                raise ValueError(f"User {user_id} already in organization {org_id}")

        # Create new org user
        new_org_user = OrgUser(
            org_id=org_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.utcnow()
        )

        # Add to organization
        org_users[org_id].append(new_org_user)
        self._save_org_users(org_users)

        logger.info(f"Added user {user_id} to org {org_id} with role {role}")
        return True

    def remove_user_from_org(self, org_id: str, user_id: str) -> bool:
        """
        Remove a user from an organization

        Args:
            org_id: Organization ID
            user_id: User ID to remove

        Returns:
            True if successful, False if user or org not found
        """
        org_users = self._load_org_users()

        if org_id not in org_users:
            logger.warning(f"Organization not found: {org_id}")
            return False

        original_count = len(org_users[org_id])
        org_users[org_id] = [
            user for user in org_users[org_id]
            if user.user_id != user_id
        ]

        if len(org_users[org_id]) == original_count:
            logger.warning(f"User {user_id} not found in org {org_id}")
            return False

        self._save_org_users(org_users)
        logger.info(f"Removed user {user_id} from org {org_id}")
        return True

    def update_user_role(self, org_id: str, user_id: str, new_role: str) -> bool:
        """
        Update a user's role in an organization

        Args:
            org_id: Organization ID
            user_id: User ID
            new_role: New role (owner, member, billing_admin)

        Returns:
            True if successful, False if user or org not found
        """
        org_users = self._load_org_users()

        if org_id not in org_users:
            logger.warning(f"Organization not found: {org_id}")
            return False

        for user in org_users[org_id]:
            if user.user_id == user_id:
                user.role = new_role
                self._save_org_users(org_users)
                logger.info(f"Updated role for user {user_id} in org {org_id} to {new_role}")
                return True

        logger.warning(f"User {user_id} not found in org {org_id}")
        return False

    def get_user_orgs(self, user_id: str) -> List[Organization]:
        """
        Get all organizations a user belongs to

        Args:
            user_id: User ID from authentication system

        Returns:
            List of Organization objects the user is a member of

        Example:
            orgs = org_manager.get_user_orgs("user_abc")
            for org in orgs:
                print(f"Member of: {org.name}")
        """
        org_users = self._load_org_users()
        orgs = self._load_organizations()

        user_org_ids = []
        for org_id, users_list in org_users.items():
            for user in users_list:
                if user.user_id == user_id:
                    user_org_ids.append(org_id)
                    break

        return [orgs[org_id] for org_id in user_org_ids if org_id in orgs]

    def get_org_users(self, org_id: str) -> List[OrgUser]:
        """
        Get all users in an organization

        Args:
            org_id: Organization ID

        Returns:
            List of OrgUser objects for the organization
        """
        org_users = self._load_org_users()
        return org_users.get(org_id, [])

    def get_user_role_in_org(self, org_id: str, user_id: str) -> Optional[str]:
        """
        Get a user's role in a specific organization

        Args:
            org_id: Organization ID
            user_id: User ID

        Returns:
            Role string or None if user not in organization
        """
        org_users = self._load_org_users()

        if org_id not in org_users:
            return None

        for user in org_users[org_id]:
            if user.user_id == user_id:
                return user.role

        return None

    # ==================== Query Operations ====================

    def list_all_organizations(self) -> List[Organization]:
        """
        Get all organizations in the system

        Returns:
            List of all Organization objects
        """
        orgs = self._load_organizations()
        return list(orgs.values())

    def search_organizations(self, query: str) -> List[Organization]:
        """
        Search organizations by name

        Args:
            query: Search query string

        Returns:
            List of matching Organization objects
        """
        orgs = self._load_organizations()
        query_lower = query.lower()

        return [
            org for org in orgs.values()
            if query_lower in org.name.lower()
        ]

    def get_organizations_by_plan(self, plan_tier: str) -> List[Organization]:
        """
        Get all organizations on a specific plan tier

        Args:
            plan_tier: Plan tier to filter by

        Returns:
            List of Organization objects on the specified plan
        """
        orgs = self._load_organizations()
        return [
            org for org in orgs.values()
            if org.plan_tier == plan_tier
        ]


# ==================== Global Singleton ====================

# Global organization manager instance
org_manager = OrgManager()

# Export for use in other modules
__all__ = ['Organization', 'OrgUser', 'OrgManager', 'org_manager']
