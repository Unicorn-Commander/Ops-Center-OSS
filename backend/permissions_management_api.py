"""
Permissions Management API for Ops Center
Provides role-based access control (RBAC) endpoints

This module implements a complete permissions management system with:
- Role management (CRUD operations)
- Resource and action definitions
- Permission matrix management
- Permission grants and revocations
- Permission checking
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Set
from datetime import datetime
from enum import Enum

router = APIRouter(prefix="/api/v1/permissions", tags=["Permissions"])


# ============================================================================
# Enums and Constants
# ============================================================================

class ResourceType(str, Enum):
    """Protected resources in the system"""
    USERS = "users"
    BILLING = "billing"
    ORGANIZATIONS = "organizations"
    SERVICES = "services"
    MODELS = "models"
    ANALYTICS = "analytics"
    SETTINGS = "settings"
    LOGS = "logs"
    API_KEYS = "api_keys"
    WEBHOOKS = "webhooks"


class ActionType(str, Enum):
    """Available actions on resources"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"


class RoleLevel(int, Enum):
    """Role hierarchy levels (lower number = more privileged)"""
    ADMIN = 1
    MODERATOR = 2
    DEVELOPER = 3
    ANALYST = 4
    VIEWER = 5


# ============================================================================
# Pydantic Models
# ============================================================================

class RoleBase(BaseModel):
    """Base role model"""
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=200)

    @validator('name')
    def validate_name(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Role name must be alphanumeric (underscores and hyphens allowed)')
        return v.lower()


class RoleCreate(RoleBase):
    """Model for creating a new role"""
    permissions: Dict[ResourceType, List[ActionType]] = Field(
        default_factory=dict,
        description="Initial permissions for the role"
    )
    level: RoleLevel = Field(
        default=RoleLevel.VIEWER,
        description="Role hierarchy level"
    )


class RoleUpdate(BaseModel):
    """Model for updating a role"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=200)
    level: Optional[RoleLevel] = None


class RoleResponse(RoleBase):
    """Role response model"""
    id: str
    level: RoleLevel
    permissions: Dict[str, List[str]]
    created_at: datetime
    updated_at: datetime
    is_system: bool = Field(
        default=False,
        description="System roles cannot be deleted"
    )


class PermissionGrant(BaseModel):
    """Model for granting permissions"""
    role_id: str
    resource: ResourceType
    actions: List[ActionType]


class PermissionRevoke(BaseModel):
    """Model for revoking permissions"""
    role_id: str
    resource: ResourceType
    actions: Optional[List[ActionType]] = Field(
        None,
        description="Specific actions to revoke. If None, revokes all actions on resource"
    )


class PermissionCheck(BaseModel):
    """Model for checking permissions"""
    role_id: str
    resource: ResourceType
    action: ActionType


class ResourceInfo(BaseModel):
    """Resource information"""
    id: str
    name: str
    description: str
    available_actions: List[str]


class ActionInfo(BaseModel):
    """Action information"""
    id: str
    name: str
    description: str


# ============================================================================
# In-Memory Data Store (Replace with database in production)
# ============================================================================

# Default permission matrix for system roles
DEFAULT_PERMISSION_MATRIX: Dict[str, Dict[str, List[str]]] = {
    "admin": {
        "users": ["read", "write", "delete", "execute"],
        "billing": ["read", "write", "delete", "execute"],
        "organizations": ["read", "write", "delete", "execute"],
        "services": ["read", "write", "delete", "execute"],
        "models": ["read", "write", "delete", "execute"],
        "analytics": ["read", "write", "delete", "execute"],
        "settings": ["read", "write", "delete", "execute"],
        "logs": ["read", "write", "delete"],
        "api_keys": ["read", "write", "delete", "execute"],
        "webhooks": ["read", "write", "delete", "execute"],
    },
    "moderator": {
        "users": ["read", "write"],
        "billing": ["read"],
        "organizations": ["read", "write"],
        "services": ["read", "write", "execute"],
        "models": ["read", "write"],
        "analytics": ["read"],
        "settings": ["read"],
        "logs": ["read"],
        "api_keys": ["read", "write"],
        "webhooks": ["read", "write"],
    },
    "developer": {
        "users": ["read"],
        "billing": [],
        "organizations": ["read"],
        "services": ["read", "execute"],
        "models": ["read", "write", "execute"],
        "analytics": ["read"],
        "settings": ["read"],
        "logs": ["read"],
        "api_keys": ["read", "write", "delete"],
        "webhooks": ["read", "write", "delete"],
    },
    "analyst": {
        "users": ["read"],
        "billing": ["read"],
        "organizations": ["read"],
        "services": ["read"],
        "models": ["read"],
        "analytics": ["read", "write", "execute"],
        "settings": ["read"],
        "logs": ["read"],
        "api_keys": [],
        "webhooks": [],
    },
    "viewer": {
        "users": ["read"],
        "billing": [],
        "organizations": ["read"],
        "services": ["read"],
        "models": ["read"],
        "analytics": ["read"],
        "settings": ["read"],
        "logs": ["read"],
        "api_keys": [],
        "webhooks": [],
    },
}

# System roles that cannot be deleted
SYSTEM_ROLES = {"admin", "moderator", "developer", "analyst", "viewer"}

# In-memory role storage
ROLES_DB: Dict[str, Dict] = {
    "admin": {
        "id": "admin",
        "name": "admin",
        "description": "Full system access with all permissions",
        "level": RoleLevel.ADMIN,
        "permissions": DEFAULT_PERMISSION_MATRIX["admin"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_system": True,
    },
    "moderator": {
        "id": "moderator",
        "name": "moderator",
        "description": "User and content management permissions",
        "level": RoleLevel.MODERATOR,
        "permissions": DEFAULT_PERMISSION_MATRIX["moderator"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_system": True,
    },
    "developer": {
        "id": "developer",
        "name": "developer",
        "description": "API and service development permissions",
        "level": RoleLevel.DEVELOPER,
        "permissions": DEFAULT_PERMISSION_MATRIX["developer"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_system": True,
    },
    "analyst": {
        "id": "analyst",
        "name": "analyst",
        "description": "Analytics and reporting permissions",
        "level": RoleLevel.ANALYST,
        "permissions": DEFAULT_PERMISSION_MATRIX["analyst"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_system": True,
    },
    "viewer": {
        "id": "viewer",
        "name": "viewer",
        "description": "Read-only access to most resources",
        "level": RoleLevel.VIEWER,
        "permissions": DEFAULT_PERMISSION_MATRIX["viewer"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_system": True,
    },
}

# Resource definitions
RESOURCES: Dict[str, ResourceInfo] = {
    "users": ResourceInfo(
        id="users",
        name="Users",
        description="User accounts and profiles",
        available_actions=["read", "write", "delete", "execute"]
    ),
    "billing": ResourceInfo(
        id="billing",
        name="Billing",
        description="Subscription plans, payments, and invoices",
        available_actions=["read", "write", "delete", "execute"]
    ),
    "organizations": ResourceInfo(
        id="organizations",
        name="Organizations",
        description="Organization management",
        available_actions=["read", "write", "delete", "execute"]
    ),
    "services": ResourceInfo(
        id="services",
        name="Services",
        description="Docker services and containers",
        available_actions=["read", "write", "delete", "execute"]
    ),
    "models": ResourceInfo(
        id="models",
        name="AI Models",
        description="LLM models and configurations",
        available_actions=["read", "write", "delete", "execute"]
    ),
    "analytics": ResourceInfo(
        id="analytics",
        name="Analytics",
        description="Usage metrics and analytics",
        available_actions=["read", "write", "delete", "execute"]
    ),
    "settings": ResourceInfo(
        id="settings",
        name="Settings",
        description="System and application settings",
        available_actions=["read", "write", "delete", "execute"]
    ),
    "logs": ResourceInfo(
        id="logs",
        name="Logs",
        description="System and application logs",
        available_actions=["read", "write", "delete"]
    ),
    "api_keys": ResourceInfo(
        id="api_keys",
        name="API Keys",
        description="API key management",
        available_actions=["read", "write", "delete", "execute"]
    ),
    "webhooks": ResourceInfo(
        id="webhooks",
        name="Webhooks",
        description="Webhook configuration and management",
        available_actions=["read", "write", "delete", "execute"]
    ),
}

# Action definitions
ACTIONS: Dict[str, ActionInfo] = {
    "read": ActionInfo(
        id="read",
        name="Read",
        description="View and retrieve resource data"
    ),
    "write": ActionInfo(
        id="write",
        name="Write",
        description="Create and update resources"
    ),
    "delete": ActionInfo(
        id="delete",
        name="Delete",
        description="Remove resources permanently"
    ),
    "execute": ActionInfo(
        id="execute",
        name="Execute",
        description="Perform actions and run operations"
    ),
}


# ============================================================================
# Helper Functions
# ============================================================================

def generate_role_id(name: str) -> str:
    """Generate a unique role ID from name"""
    return name.lower().replace(' ', '_')


def validate_role_exists(role_id: str) -> Dict:
    """Validate that a role exists and return it"""
    if role_id not in ROLES_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_id}' not found"
        )
    return ROLES_DB[role_id]


def validate_resource_exists(resource: str) -> None:
    """Validate that a resource exists"""
    if resource not in RESOURCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource: {resource}"
        )


def validate_action_exists(action: str) -> None:
    """Validate that an action exists"""
    if action not in ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}"
        )


# ============================================================================
# API Endpoints
# ============================================================================

# 1. List all roles
@router.get("/roles", response_model=List[RoleResponse])
async def list_roles():
    """
    Get list of all roles in the system

    Returns a list of all roles with their permissions and metadata.
    System roles (admin, moderator, etc.) are marked with is_system=True.
    """
    roles = []
    for role_data in ROLES_DB.values():
        roles.append(RoleResponse(**role_data))

    # Sort by level (most privileged first)
    roles.sort(key=lambda r: r.level)

    return roles


# 2. Create new role
@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(role: RoleCreate):
    """
    Create a new custom role

    Creates a new role with specified permissions. Role names must be unique.
    System role names (admin, moderator, etc.) are reserved.
    """
    role_id = generate_role_id(role.name)

    # Check if role already exists
    if role_id in ROLES_DB:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role '{role_id}' already exists"
        )

    # Prevent creating roles with system role names
    if role_id in SYSTEM_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create role with reserved name: {role_id}"
        )

    # Validate permissions
    permissions_dict = {}
    for resource, actions in role.permissions.items():
        resource_str = resource.value
        validate_resource_exists(resource_str)

        # Validate all actions exist for this resource
        available_actions = RESOURCES[resource_str].available_actions
        for action in actions:
            action_str = action.value
            validate_action_exists(action_str)
            if action_str not in available_actions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Action '{action_str}' not available for resource '{resource_str}'"
                )

        permissions_dict[resource_str] = [a.value for a in actions]

    # Create role
    now = datetime.utcnow()
    new_role = {
        "id": role_id,
        "name": role.name.lower(),
        "description": role.description,
        "level": role.level,
        "permissions": permissions_dict,
        "created_at": now,
        "updated_at": now,
        "is_system": False,
    }

    ROLES_DB[role_id] = new_role

    return RoleResponse(**new_role)


# 3. Update role
@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(role_id: str, role_update: RoleUpdate):
    """
    Update an existing role

    Updates role metadata (name, description, level).
    Use /permissions/grant and /permissions/revoke to modify permissions.
    System roles cannot have their level changed.
    """
    role = validate_role_exists(role_id)

    # Update fields
    if role_update.name is not None:
        new_id = generate_role_id(role_update.name)
        if new_id != role_id and new_id in ROLES_DB:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role '{new_id}' already exists"
            )
        role["name"] = role_update.name.lower()

    if role_update.description is not None:
        role["description"] = role_update.description

    if role_update.level is not None:
        if role["is_system"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change level of system roles"
            )
        role["level"] = role_update.level

    role["updated_at"] = datetime.utcnow()

    return RoleResponse(**role)


# 4. Delete role
@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: str):
    """
    Delete a role

    Removes a role from the system. System roles cannot be deleted.
    """
    role = validate_role_exists(role_id)

    if role["is_system"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system roles"
        )

    del ROLES_DB[role_id]

    return None


# 5. List protected resources
@router.get("/resources", response_model=List[ResourceInfo])
async def list_resources():
    """
    Get list of all protected resources

    Returns all resources that can have permissions assigned,
    along with their available actions.
    """
    return list(RESOURCES.values())


# 6. List available actions
@router.get("/actions", response_model=List[ActionInfo])
async def list_actions():
    """
    Get list of all available actions

    Returns all actions that can be performed on resources:
    - read: View and retrieve data
    - write: Create and update resources
    - delete: Remove resources
    - execute: Perform operations
    """
    return list(ACTIONS.values())


# 7. Get full permission matrix
@router.get("/matrix")
async def get_permission_matrix():
    """
    Get the complete permission matrix

    Returns a matrix showing all roles and their permissions
    on each resource. Useful for visualizing the full RBAC structure.
    """
    matrix = {}

    for role_id, role_data in ROLES_DB.items():
        matrix[role_id] = {
            "role_info": {
                "name": role_data["name"],
                "description": role_data["description"],
                "level": role_data["level"],
                "is_system": role_data["is_system"],
            },
            "permissions": role_data["permissions"]
        }

    return {
        "matrix": matrix,
        "resources": {k: v.dict() for k, v in RESOURCES.items()},
        "actions": {k: v.dict() for k, v in ACTIONS.items()},
    }


# 8. Grant permission to role
@router.post("/grant", response_model=RoleResponse)
async def grant_permission(grant: PermissionGrant):
    """
    Grant permissions to a role

    Adds specified actions on a resource to a role's permissions.
    If the role already has some of these permissions, they are merged.
    """
    role = validate_role_exists(grant.role_id)

    resource_str = grant.resource.value
    validate_resource_exists(resource_str)

    # Validate actions
    available_actions = RESOURCES[resource_str].available_actions
    for action in grant.actions:
        action_str = action.value
        validate_action_exists(action_str)
        if action_str not in available_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action '{action_str}' not available for resource '{resource_str}'"
            )

    # Get existing permissions for this resource
    current_permissions = set(role["permissions"].get(resource_str, []))

    # Add new actions
    new_actions = set(a.value for a in grant.actions)
    current_permissions.update(new_actions)

    # Update role permissions
    role["permissions"][resource_str] = sorted(list(current_permissions))
    role["updated_at"] = datetime.utcnow()

    return RoleResponse(**role)


# 9. Revoke permission from role
@router.post("/revoke", response_model=RoleResponse)
async def revoke_permission(revoke: PermissionRevoke):
    """
    Revoke permissions from a role

    Removes specified actions on a resource from a role's permissions.
    If actions is None, removes all permissions on the resource.
    """
    role = validate_role_exists(revoke.role_id)

    resource_str = revoke.resource.value
    validate_resource_exists(resource_str)

    # If no current permissions on this resource, nothing to revoke
    if resource_str not in role["permissions"]:
        return RoleResponse(**role)

    current_permissions = set(role["permissions"][resource_str])

    # If no specific actions provided, revoke all
    if revoke.actions is None:
        role["permissions"][resource_str] = []
    else:
        # Revoke specific actions
        actions_to_revoke = set(a.value for a in revoke.actions)
        current_permissions -= actions_to_revoke
        role["permissions"][resource_str] = sorted(list(current_permissions))

    # Remove empty permission entries
    if not role["permissions"][resource_str]:
        del role["permissions"][resource_str]

    role["updated_at"] = datetime.utcnow()

    return RoleResponse(**role)


# 10. Check if role has permission
@router.post("/check")
async def check_permission(check: PermissionCheck):
    """
    Check if a role has a specific permission

    Returns whether the role has permission to perform the specified
    action on the specified resource.
    """
    role = validate_role_exists(check.role_id)

    resource_str = check.resource.value
    action_str = check.action.value

    validate_resource_exists(resource_str)
    validate_action_exists(action_str)

    # Check if role has permission
    has_permission = False
    if resource_str in role["permissions"]:
        has_permission = action_str in role["permissions"][resource_str]

    return {
        "role_id": check.role_id,
        "resource": resource_str,
        "action": action_str,
        "has_permission": has_permission,
        "role_level": role["level"],
        "role_name": role["name"]
    }


# ============================================================================
# Additional Utility Endpoints
# ============================================================================

@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(role_id: str):
    """
    Get a specific role by ID

    Returns detailed information about a role including all its permissions.
    """
    role = validate_role_exists(role_id)
    return RoleResponse(**role)


@router.get("/roles/{role_id}/permissions")
async def get_role_permissions(role_id: str):
    """
    Get all permissions for a specific role

    Returns a detailed breakdown of the role's permissions,
    organized by resource with human-readable descriptions.
    """
    role = validate_role_exists(role_id)

    detailed_permissions = {}
    for resource_id, actions in role["permissions"].items():
        if resource_id in RESOURCES:
            detailed_permissions[resource_id] = {
                "resource_info": RESOURCES[resource_id].dict(),
                "granted_actions": [
                    {
                        "action": action,
                        "description": ACTIONS[action].description if action in ACTIONS else ""
                    }
                    for action in actions
                ]
            }

    return {
        "role_id": role_id,
        "role_name": role["name"],
        "role_level": role["level"],
        "permissions": detailed_permissions
    }


@router.get("/stats")
async def get_permission_stats():
    """
    Get statistics about the permission system

    Returns counts and summary information about roles, resources,
    and permission assignments.
    """
    total_roles = len(ROLES_DB)
    system_roles = sum(1 for r in ROLES_DB.values() if r["is_system"])
    custom_roles = total_roles - system_roles

    # Count total permission grants
    total_grants = sum(
        len(actions)
        for role in ROLES_DB.values()
        for actions in role["permissions"].values()
    )

    return {
        "roles": {
            "total": total_roles,
            "system": system_roles,
            "custom": custom_roles
        },
        "resources": len(RESOURCES),
        "actions": len(ACTIONS),
        "total_permission_grants": total_grants,
        "roles_by_level": {
            level.name.lower(): sum(
                1 for r in ROLES_DB.values() if r["level"] == level
            )
            for level in RoleLevel
        }
    }
