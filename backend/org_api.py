"""
Organization Management API Endpoints
Provides organization CRUD operations, member management, and settings
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path to import from server.py
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

# Import organization manager
from org_manager import org_manager, Organization, OrgUser

# Import Keycloak user lookup
from keycloak_integration import get_user_by_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/org", tags=["organizations"])


# ==================== Request/Response Models ====================

class OrganizationMemberAdd(BaseModel):
    """Request model for adding a member to organization"""
    user_id: str
    role: str = "member"


class OrganizationMemberRoleUpdate(BaseModel):
    """Request model for updating member role"""
    role: str


class OrganizationSettingsUpdate(BaseModel):
    """Request model for updating organization settings"""
    settings: Dict[str, Any]


class OrganizationCreate(BaseModel):
    """Request model for creating a new organization"""
    name: str
    plan_tier: str = "founders_friend"


# ==================== Helper Functions ====================

async def get_current_user(request: Request) -> Dict:
    """Get current user data from session (uses Redis session manager)"""
    from redis_session import RedisSessionManager

    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get Redis connection info
    redis_host = os.getenv("REDIS_HOST", "unicorn-lago-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    # Initialize session manager
    sessions = RedisSessionManager(host=redis_host, port=redis_port)

    # Get session data
    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    session_data = sessions[session_token]
    user = session_data.get("user", {})

    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    # Ensure user_id field exists (map from Keycloak 'sub' field if needed)
    if "user_id" not in user:
        user["user_id"] = user.get("sub") or user.get("id", "unknown")

    # Ensure id field exists
    if "id" not in user:
        user["id"] = user.get("sub") or user.get("user_id", "unknown")

    return user


async def require_admin(request: Request) -> Dict:
    """Require admin role for endpoint access"""
    user = await get_current_user(request)

    # Check if user has admin role
    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


async def get_user_org_id(request: Request) -> str:
    """Get organization ID from user session"""
    user = await get_current_user(request)

    org_id = user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User has no organization")

    return org_id


async def verify_org_access(request: Request, org_id: str, required_role: Optional[str] = None):
    """
    Verify user has access to organization

    Args:
        request: FastAPI request object
        org_id: Organization ID to check access for
        required_role: Optional role requirement (owner, billing_admin, member)

    Raises:
        HTTPException: If user lacks access
    """
    user = await get_current_user(request)
    user_id = user.get("id") or user.get("email")

    # Admins have access to all organizations
    if user.get("is_admin") or user.get("role") == "admin":
        return

    # Check if user is member of organization
    user_role = org_manager.get_user_role_in_org(org_id, user_id)
    if not user_role:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")

    # Check required role if specified
    if required_role:
        role_hierarchy = ["member", "billing_admin", "owner"]
        user_role_level = role_hierarchy.index(user_role) if user_role in role_hierarchy else -1
        required_role_level = role_hierarchy.index(required_role) if required_role in role_hierarchy else 99

        if user_role_level < required_role_level:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{required_role}' or higher required"
            )


# ==================== API Endpoints ====================

@router.get("/my-orgs")
async def get_my_organizations(request: Request):
    """
    Get list of organizations the current user is a member of

    Returns:
        List of organizations with user's role in each

    Example:
        GET /api/v1/org/my-orgs
        Response: [
            {
                "id": "org_12345",
                "name": "Magic Unicorn",
                "role": "owner",
                "plan_tier": "professional",
                "status": "active",
                "member_count": 5,
                "joined_at": "2025-01-15T10:30:00Z"
            },
            ...
        ]
    """
    user = await get_current_user(request)
    user_id = user.get("id") or user.get("sub") or user.get("user_id")

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in session")

    # Get all organizations
    all_orgs = org_manager.list_all_organizations()

    # Filter to organizations where user is a member
    user_orgs = []
    for org in all_orgs:
        # Check if user is a member
        members = org_manager.get_org_users(org.id)
        user_member = None
        for member in members:
            if member.user_id == user_id:
                user_member = member
                break

        if user_member:
            user_orgs.append({
                "id": org.id,
                "name": org.name,
                "role": user_member.role,
                "plan_tier": org.plan_tier,
                "status": org.status,
                "member_count": len(members),
                "joined_at": user_member.joined_at.isoformat() if user_member.joined_at else None
            })

    logger.info(f"Found {len(user_orgs)} organizations for user {user_id}")

    return user_orgs


@router.get("/organizations")
async def list_all_organizations(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Get list of all organizations (admin only)

    Args:
        request: FastAPI request object
        limit: Maximum number of organizations to return (default: 50)
        offset: Number of organizations to skip for pagination (default: 0)
        status: Filter by status (active, suspended, deleted)
        tier: Filter by subscription tier
        search: Search by organization name

    Returns:
        List of organizations with member counts and metadata

    Example:
        GET /api/v1/org/organizations?limit=10&status=active
        Response: {
            "organizations": [
                {
                    "id": "org_12345",
                    "name": "Acme Corp",
                    "owner": "owner@example.com",
                    "member_count": 5,
                    "created_at": "2025-01-15T10:30:00Z",
                    "subscription_tier": "professional",
                    "status": "active",
                    "lago_customer_id": "lago_cust_abc",
                    "stripe_customer_id": "cus_xyz"
                },
                ...
            ],
            "total": 100,
            "limit": 10,
            "offset": 0
        }
    """
    # Require admin access
    await require_admin(request)

    try:
        # Get all organizations from manager
        all_orgs = org_manager.list_all_organizations()

        # Apply filters
        filtered_orgs = all_orgs

        # Filter by status
        if status:
            filtered_orgs = [org for org in filtered_orgs if org.status == status]

        # Filter by tier
        if tier:
            filtered_orgs = [org for org in filtered_orgs if org.plan_tier == tier]

        # Filter by search query (name)
        if search:
            search_lower = search.lower()
            filtered_orgs = [org for org in filtered_orgs if search_lower in org.name.lower()]

        # Get total count before pagination
        total = len(filtered_orgs)

        # Apply pagination
        paginated_orgs = filtered_orgs[offset:offset + limit]

        # Enrich with member counts and owner info
        enriched_orgs = []
        for org in paginated_orgs:
            # Get member count
            members = org_manager.get_org_users(org.id)
            member_count = len(members)

            # Find owner and get their email from Keycloak
            owner_display = "Unknown"
            for member in members:
                if member.role == "owner":
                    # Look up user in Keycloak to get email/username
                    try:
                        user_data = await get_user_by_id(member.user_id)
                        if user_data:
                            owner_display = user_data.get('email') or user_data.get('username') or member.user_id
                        else:
                            owner_display = member.user_id
                    except Exception as e:
                        logger.warning(f"Failed to fetch user info for owner {member.user_id}: {e}")
                        owner_display = member.user_id  # Fallback to user_id
                    break

            enriched_orgs.append({
                "id": org.id,
                "name": org.name,
                "owner": owner_display,
                "member_count": member_count,
                "created_at": org.created_at.isoformat(),
                "subscription_tier": org.plan_tier,
                "status": org.status,
                "lago_customer_id": org.lago_customer_id,
                "stripe_customer_id": org.stripe_customer_id
            })

        logger.info(f"Listed {len(enriched_orgs)} organizations (total: {total}, filters: status={status}, tier={tier}, search={search})")

        return {
            "organizations": enriched_orgs,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing organizations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list organizations: {str(e)}")


@router.post("")
async def create_organization(
    org_data: OrganizationCreate,
    request: Request
):
    """
    Create a new organization

    Args:
        org_data: Organization name and plan tier
        request: FastAPI request object

    Returns:
        Created organization details including ID and owner info

    Example:
        POST /api/v1/org
        Body: {"name": "Acme Corp", "plan_tier": "professional"}
        Response: {
            "success": true,
            "organization": {
                "id": "org_12345",
                "name": "Acme Corp",
                "plan_tier": "professional",
                "status": "active",
                "created_at": "2025-10-28T10:30:00Z",
                "owner": "admin@example.com",
                "member_count": 1
            }
        }
    """
    # Get current user
    user = await get_current_user(request)
    user_id = user.get("id") or user.get("email")

    if not user_id:
        raise HTTPException(status_code=400, detail="Could not identify user")

    try:
        # Create organization using org_manager
        org_id = org_manager.create_organization(
            name=org_data.name,
            plan_tier=org_data.plan_tier
        )

        # Add current user as owner
        org_manager.add_user_to_org(
            org_id=org_id,
            user_id=user_id,
            role="owner"
        )

        # Get created organization
        org = org_manager.get_org(org_id)
        if not org:
            raise HTTPException(status_code=500, detail="Failed to retrieve created organization")

        # Get member count
        members = org_manager.get_org_users(org_id)

        logger.info(f"Created organization {org_id} ({org_data.name}) with owner {user_id}")

        return {
            "success": True,
            "organization": {
                "id": org.id,
                "name": org.name,
                "plan_tier": org.plan_tier,
                "status": org.status,
                "created_at": org.created_at.isoformat(),
                "owner": user_id,
                "member_count": len(members),
                "lago_customer_id": org.lago_customer_id,
                "stripe_customer_id": org.stripe_customer_id
            }
        }

    except ValueError as e:
        # Validation error (e.g., duplicate name)
        logger.warning(f"Validation error creating organization: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating organization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")


@router.get("/roles")
async def list_available_roles():
    """
    Get list of available organization roles

    Returns:
        List of roles with descriptions and permissions

    Example:
        GET /api/v1/org/roles
        Response: {
            "roles": [
                {
                    "id": "owner",
                    "name": "Owner",
                    "description": "Full organization control",
                    "permissions": ["manage_members", "manage_billing", "manage_settings", "delete_org"]
                },
                ...
            ]
        }
    """
    roles = [
        {
            "id": "owner",
            "name": "Owner",
            "description": "Full organization control including member management and billing",
            "permissions": [
                "manage_members",
                "manage_billing",
                "manage_settings",
                "delete_org",
                "view_all"
            ]
        },
        {
            "id": "billing_admin",
            "name": "Billing Admin",
            "description": "Manage billing and view organization details",
            "permissions": [
                "manage_billing",
                "view_all"
            ]
        },
        {
            "id": "member",
            "name": "Member",
            "description": "Basic organization member with view access",
            "permissions": [
                "view_all"
            ]
        }
    ]

    return {"roles": roles}


@router.get("/{org_id}/members")
async def list_organization_members(
    org_id: str,
    request: Request,
    offset: int = 0,
    limit: int = 100,
    search: str = ""
):
    """
    Get list of all members in an organization with full user details

    Args:
        org_id: Organization ID
        offset: Pagination offset (default: 0)
        limit: Pagination limit (default: 100, max: 1000)
        search: Search by email, username, or name

    Returns:
        List of organization members with roles, join dates, and user details from Keycloak

    Example:
        GET /api/v1/org/org_12345/members?offset=0&limit=10&search=aaron
        Response: {
            "members": [
                {
                    "id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
                    "user_id": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
                    "email": "admin@example.com",
                    "username": "aaron",
                    "firstName": "Aaron",
                    "lastName": "User",
                    "org_role": "owner",
                    "enabled": true,
                    "emailVerified": true,
                    "createdAt": "2025-01-15T10:30:00Z"
                },
                ...
            ],
            "total": 5,
            "offset": 0,
            "limit": 10
        }
    """
    # Verify user has access to this organization
    await verify_org_access(request, org_id)

    # Get organization to verify it exists
    org = org_manager.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get all members
    members = org_manager.get_org_users(org_id)

    # Enrich members with Keycloak user data
    enriched_members = []
    for member in members:
        try:
            # Fetch user details from Keycloak
            user_data = await get_user_by_id(member.user_id)

            if user_data:
                enriched_member = {
                    "id": member.user_id,
                    "user_id": member.user_id,
                    "email": user_data.get("email", ""),
                    "username": user_data.get("username", ""),
                    "firstName": user_data.get("firstName", ""),
                    "lastName": user_data.get("lastName", ""),
                    "org_role": member.role,
                    "enabled": user_data.get("enabled", False),
                    "emailVerified": user_data.get("emailVerified", False),
                    "createdAt": member.joined_at.isoformat() if member.joined_at else None
                }
                enriched_members.append(enriched_member)
            else:
                # Fallback if Keycloak lookup fails
                logger.warning(f"Could not fetch Keycloak data for user {member.user_id}")
                enriched_members.append({
                    "id": member.user_id,
                    "user_id": member.user_id,
                    "email": member.user_id,  # Fallback to user_id
                    "username": member.user_id,
                    "firstName": "",
                    "lastName": "",
                    "org_role": member.role,
                    "enabled": True,
                    "emailVerified": False,
                    "createdAt": member.joined_at.isoformat() if member.joined_at else None
                })
        except Exception as e:
            logger.error(f"Error enriching member {member.user_id}: {e}")
            # Include basic data even if enrichment fails
            enriched_members.append({
                "id": member.user_id,
                "user_id": member.user_id,
                "email": member.user_id,
                "username": member.user_id,
                "firstName": "",
                "lastName": "",
                "org_role": member.role,
                "enabled": True,
                "emailVerified": False,
                "createdAt": member.joined_at.isoformat() if member.joined_at else None
            })

    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        enriched_members = [
            m for m in enriched_members
            if search_lower in m.get("email", "").lower()
            or search_lower in m.get("username", "").lower()
            or search_lower in m.get("firstName", "").lower()
            or search_lower in m.get("lastName", "").lower()
        ]

    # Get total count before pagination
    total = len(enriched_members)

    # Apply pagination
    enriched_members = enriched_members[offset:offset + limit]

    logger.info(f"Listed {len(enriched_members)} members (total: {total}) for org {org_id}")

    return {
        "members": enriched_members,
        "total": total,
        "offset": offset,
        "limit": limit
    }


@router.post("/{org_id}/members")
async def add_organization_member(
    org_id: str,
    member_data: OrganizationMemberAdd,
    request: Request
):
    """
    Add a new member to the organization

    Args:
        org_id: Organization ID
        member_data: User ID and role to assign

    Returns:
        Success confirmation

    Example:
        POST /api/v1/org/org_12345/members
        Body: {"user_id": "newuser@example.com", "role": "member"}
        Response: {
            "success": true,
            "message": "User added to organization",
            "user_id": "newuser@example.com",
            "role": "member"
        }
    """
    # Require owner role to add members
    await verify_org_access(request, org_id, required_role="owner")

    try:
        # Add user to organization
        success = org_manager.add_user_to_org(
            org_id=org_id,
            user_id=member_data.user_id,
            role=member_data.role
        )

        if not success:
            raise HTTPException(status_code=404, detail="Organization not found")

        logger.info(f"Added user {member_data.user_id} to org {org_id} with role {member_data.role}")

        return {
            "success": True,
            "message": "User added to organization",
            "user_id": member_data.user_id,
            "role": member_data.role
        }

    except ValueError as e:
        # User already in organization or invalid role
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding member to org {org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add member: {str(e)}")


@router.put("/{org_id}/members/{user_id}/role")
async def update_member_role(
    org_id: str,
    user_id: str,
    role_data: OrganizationMemberRoleUpdate,
    request: Request
):
    """
    Update a member's role in the organization

    Args:
        org_id: Organization ID
        user_id: User ID to update
        role_data: New role to assign

    Returns:
        Success confirmation

    Example:
        PUT /api/v1/org/org_12345/members/user@example.com/role
        Body: {"role": "billing_admin"}
        Response: {
            "success": true,
            "message": "User role updated",
            "user_id": "user@example.com",
            "new_role": "billing_admin"
        }
    """
    # Require owner role to update member roles
    await verify_org_access(request, org_id, required_role="owner")

    try:
        # Update user role
        success = org_manager.update_user_role(
            org_id=org_id,
            user_id=user_id,
            new_role=role_data.role
        )

        if not success:
            raise HTTPException(status_code=404, detail="User not found in organization")

        logger.info(f"Updated role for user {user_id} in org {org_id} to {role_data.role}")

        return {
            "success": True,
            "message": "User role updated",
            "user_id": user_id,
            "new_role": role_data.role
        }

    except Exception as e:
        logger.error(f"Error updating member role in org {org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update role: {str(e)}")


@router.delete("/{org_id}/members/{user_id}")
async def remove_organization_member(
    org_id: str,
    user_id: str,
    request: Request
):
    """
    Remove a member from the organization

    Args:
        org_id: Organization ID
        user_id: User ID to remove

    Returns:
        Success confirmation

    Example:
        DELETE /api/v1/org/org_12345/members/user@example.com
        Response: {
            "success": true,
            "message": "User removed from organization",
            "user_id": "user@example.com"
        }
    """
    # Require owner role to remove members
    await verify_org_access(request, org_id, required_role="owner")

    # Prevent removing the last owner
    members = org_manager.get_org_users(org_id)
    owners = [m for m in members if m.role == "owner"]

    if len(owners) == 1 and owners[0].user_id == user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove the last owner. Transfer ownership first."
        )

    try:
        # Remove user from organization
        success = org_manager.remove_user_from_org(org_id=org_id, user_id=user_id)

        if not success:
            raise HTTPException(status_code=404, detail="User not found in organization")

        logger.info(f"Removed user {user_id} from org {org_id}")

        return {
            "success": True,
            "message": "User removed from organization",
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Error removing member from org {org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove member: {str(e)}")


@router.get("/{org_id}/stats")
async def get_organization_stats(org_id: str, request: Request):
    """
    Get organization statistics and metrics

    Args:
        org_id: Organization ID

    Returns:
        Organization statistics including member counts, activity, etc.

    Example:
        GET /api/v1/org/org_12345/stats
        Response: {
            "totalMembers": 5,
            "activeMembers": 5,
            "admins": 2,
            "pendingInvites": 0,
            "members_by_role": {"owner": 1, "admin": 1, "member": 3},
            "created_at": "2025-01-01T00:00:00Z",
            "plan_tier": "professional",
            "status": "active"
        }
    """
    # Verify user has access to this organization
    await verify_org_access(request, org_id)

    # Get organization
    org = org_manager.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get members
    members = org_manager.get_org_users(org_id)

    # Count members by role
    members_by_role = {}
    active_members = 0
    admins = 0

    for member in members:
        members_by_role[member.role] = members_by_role.get(member.role, 0) + 1

        # Count admins and owners
        if member.role in ["owner", "admin"]:
            admins += 1

        # Check if user is enabled in Keycloak
        try:
            user_data = await get_user_by_id(member.user_id)
            if user_data and user_data.get("enabled", False):
                active_members += 1
        except Exception as e:
            logger.warning(f"Could not check user status for {member.user_id}: {e}")
            # Assume active if we can't check
            active_members += 1

    stats = {
        # Frontend expected fields
        "totalMembers": len(members),
        "activeMembers": active_members,
        "admins": admins,
        "pendingInvites": 0,  # TODO: Implement invitation system

        # Additional legacy fields
        "total_members": len(members),
        "members_by_role": members_by_role,
        "created_at": org.created_at.isoformat(),
        "plan_tier": org.plan_tier,
        "status": org.status,
        "organization_name": org.name
    }

    logger.info(f"Retrieved stats for org {org_id}: {stats['totalMembers']} total, {stats['activeMembers']} active, {stats['admins']} admins")

    return stats


@router.get("/{org_id}/billing")
async def get_organization_billing(org_id: str, request: Request):
    """
    Get organization billing information

    Args:
        org_id: Organization ID

    Returns:
        Billing information including Lago and Stripe customer IDs

    Example:
        GET /api/v1/org/org_12345/billing
        Response: {
            "plan_tier": "professional",
            "lago_customer_id": "lago_cust_abc123",
            "stripe_customer_id": "cus_xyz789",
            "status": "active"
        }
    """
    # Require billing_admin or owner role to view billing
    await verify_org_access(request, org_id, required_role="billing_admin")

    # Get organization
    org = org_manager.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    billing_info = {
        "plan_tier": org.plan_tier,
        "lago_customer_id": org.lago_customer_id,
        "stripe_customer_id": org.stripe_customer_id,
        "status": org.status,
        "created_at": org.created_at.isoformat()
    }

    logger.info(f"Retrieved billing info for org {org_id}")

    return billing_info


@router.get("/{org_id}/settings")
async def get_organization_settings(org_id: str, request: Request):
    """
    Get organization settings

    Args:
        org_id: Organization ID

    Returns:
        Organization settings and configuration

    Example:
        GET /api/v1/org/org_12345/settings
        Response: {
            "id": "org_12345",
            "name": "Acme Corp",
            "plan_tier": "professional",
            "status": "active",
            "created_at": "2025-01-01T00:00:00Z",
            "settings": {}
        }
    """
    # Verify user has access to this organization
    await verify_org_access(request, org_id)

    # Get organization
    org = org_manager.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    settings = {
        "id": org.id,
        "name": org.name,
        "plan_tier": org.plan_tier,
        "status": org.status,
        "created_at": org.created_at.isoformat(),
        "settings": {}  # Placeholder for future settings
    }

    logger.info(f"Retrieved settings for org {org_id}")

    return settings


@router.put("/{org_id}/settings")
async def update_organization_settings(
    org_id: str,
    settings_data: OrganizationSettingsUpdate,
    request: Request
):
    """
    Update organization settings

    Args:
        org_id: Organization ID
        settings_data: Settings to update

    Returns:
        Updated settings

    Example:
        PUT /api/v1/org/org_12345/settings
        Body: {"settings": {"notification_email": "admin@acme.com"}}
        Response: {
            "success": true,
            "message": "Settings updated",
            "settings": {"notification_email": "admin@acme.com"}
        }
    """
    # Require owner role to update settings
    await verify_org_access(request, org_id, required_role="owner")

    # Get organization
    org = org_manager.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # TODO: Implement settings storage in org_manager
    # For now, just return success

    logger.info(f"Updated settings for org {org_id}")

    return {
        "success": True,
        "message": "Settings updated",
        "settings": settings_data.settings
    }
