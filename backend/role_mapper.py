"""
Keycloak/Authentik Role Mapper for UC-1 Pro Ops Center

Maps Keycloak/Authentik user groups and roles to ops-center role hierarchy:
- admin: Full system access
- power_user: Advanced features and configuration
- user: Standard user access
- viewer: Read-only access (default fallback)
"""

import logging
import os
from typing import Dict, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

# Role hierarchy for ops-center
ROLE_HIERARCHY = ["admin", "power_user", "user", "viewer"]

# Keycloak/Authentik group and role mappings
ROLE_MAPPINGS = {
    "admin": [
        "admins",           # Keycloak group
        "admin",            # Keycloak role
        "administrators",   # Alternative group name
        "ops-center-admin", # Application-specific group
        "uc1-admins"        # UC-1 Pro admin group
    ],
    "power_user": [
        "power_users",      # Keycloak group
        "power_user",       # Keycloak role
        "powerusers",       # Alternative spelling
        "ops-center-poweruser",  # Application-specific group
        "uc1-power-users"   # UC-1 Pro power user group
    ],
    "user": [
        "users",            # Keycloak group
        "user",             # Keycloak role
        "standard_users",   # Alternative group name
        "ops-center-user",  # Application-specific group
        "uc1-users"         # UC-1 Pro user group
    ],
    "viewer": [
        "viewers",          # Keycloak group
        "viewer",           # Keycloak role
        "read_only",        # Alternative group name
        "ops-center-viewer", # Application-specific group
        "uc1-viewers"       # UC-1 Pro viewer group
    ]
}


def extract_groups_from_user_info(user_info: Dict) -> List[str]:
    """
    Extract groups from Keycloak/Authentik user info response.

    Keycloak/Authentik can return groups in various formats:
    - groups: ["group1", "group2"]
    - groups: [{"name": "group1"}, {"name": "group2"}]
    - ak_groups: ["group1", "group2"]  # Authentik-specific

    Args:
        user_info: User info dict from Keycloak/Authentik userinfo endpoint

    Returns:
        List of group names (normalized to lowercase)
    """
    groups = []

    # Check for standard 'groups' claim
    if "groups" in user_info:
        raw_groups = user_info["groups"]
        if isinstance(raw_groups, list):
            for group in raw_groups:
                if isinstance(group, str):
                    groups.append(group.lower())
                elif isinstance(group, dict) and "name" in group:
                    groups.append(group["name"].lower())

    # Check for Authentik-specific 'ak_groups' claim
    if "ak_groups" in user_info:
        raw_groups = user_info["ak_groups"]
        if isinstance(raw_groups, list):
            for group in raw_groups:
                if isinstance(group, str):
                    groups.append(group.lower())
                elif isinstance(group, dict) and "name" in group:
                    groups.append(group["name"].lower())

    # Check for 'realm_access.roles' (Keycloak-specific)
    if "realm_access" in user_info and isinstance(user_info["realm_access"], dict):
        realm_roles = user_info["realm_access"].get("roles", [])
        if isinstance(realm_roles, list):
            groups.extend([role.lower() for role in realm_roles if isinstance(role, str)])

    # Check for 'resource_access' (Keycloak client roles)
    if "resource_access" in user_info and isinstance(user_info["resource_access"], dict):
        for client, client_data in user_info["resource_access"].items():
            if isinstance(client_data, dict) and "roles" in client_data:
                client_roles = client_data["roles"]
                if isinstance(client_roles, list):
                    groups.extend([role.lower() for role in client_roles if isinstance(role, str)])

    # Remove duplicates
    return list(set(groups))


def map_keycloak_role(user_info: Dict) -> str:
    """
    Map Keycloak/Authentik user info to ops-center role.

    Role assignment logic:
    1. Check for special admin usernames (akadmin, admin)
    2. Extract all groups and roles from user info
    3. Check against role mappings in priority order (admin > power_user > user > viewer)
    4. Return highest priority role found
    5. Default to 'viewer' if no matches found

    Args:
        user_info: User info dict from Keycloak/Authentik userinfo endpoint

    Returns:
        Role string: 'admin', 'power_user', 'user', or 'viewer'
    """
    username = user_info.get("preferred_username") or user_info.get("username") or user_info.get("email", "unknown")

    # Special handling for admin usernames and emails
    # Configure via ADMIN_USERNAMES and ADMIN_EMAILS environment variables (comma-separated)
    admin_identifiers = os.getenv("ADMIN_USERNAMES", "akadmin,admin,administrator").split(",")
    admin_identifiers = [a.strip().lower() for a in admin_identifiers if a.strip()]
    admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")
    admin_emails = [e.strip().lower() for e in admin_emails if e.strip()]

    email = user_info.get("email", "").lower()

    if username.lower() in admin_identifiers or (admin_emails and email in admin_emails):
        logger.info(f"User '{username}' ({email}) is a special admin account, granting admin role")
        return "admin"

    # Extract all groups/roles from user info
    user_groups = extract_groups_from_user_info(user_info)

    logger.info(f"Mapping role for user '{username}'")
    logger.debug(f"User groups/roles found: {user_groups}")

    # If user_info already has a 'role' field from previous mapping, log it
    if "role" in user_info:
        logger.debug(f"Existing role in user_info: {user_info['role']}")

    # Check role mappings in priority order
    for role in ROLE_HIERARCHY:
        role_identifiers = ROLE_MAPPINGS.get(role, [])
        for identifier in role_identifiers:
            if identifier.lower() in user_groups:
                logger.info(f"User '{username}' mapped to role '{role}' via group/role '{identifier}'")
                return role

    # Default to viewer if no role found
    logger.warning(f"No role mapping found for user '{username}', defaulting to 'viewer'")
    logger.debug(f"Available groups were: {user_groups}")

    return "viewer"


def add_role_to_user_info(user_info: Dict) -> Dict:
    """
    Add mapped role to user_info dict if not already present.

    This function modifies the user_info dict in place and returns it.

    Args:
        user_info: User info dict from Keycloak/Authentik

    Returns:
        Updated user_info dict with 'role' field
    """
    if "role" not in user_info:
        mapped_role = map_keycloak_role(user_info)
        user_info["role"] = mapped_role
        logger.info(f"Added role '{mapped_role}' to user_info")
    else:
        logger.debug(f"Role already present in user_info: {user_info['role']}")

    return user_info


def get_role_display_name(role: str) -> str:
    """
    Get human-readable display name for role.

    Args:
        role: Role string

    Returns:
        Display name for role
    """
    display_names = {
        "admin": "Administrator",
        "power_user": "Power User",
        "user": "User",
        "viewer": "Viewer"
    }
    return display_names.get(role, role.title())


def validate_role(role: str) -> bool:
    """
    Validate if a role is valid for ops-center.

    Args:
        role: Role string to validate

    Returns:
        True if role is valid, False otherwise
    """
    return role in ROLE_HIERARCHY


if __name__ == "__main__":
    # Test cases for role mapping
    test_cases = [
        {
            "name": "Admin user with groups",
            "user_info": {
                "username": "admin_user",
                "groups": ["admins", "users"]
            },
            "expected": "admin"
        },
        {
            "name": "Power user with Authentik groups",
            "user_info": {
                "username": "power_user",
                "ak_groups": ["power_users"]
            },
            "expected": "power_user"
        },
        {
            "name": "Standard user",
            "user_info": {
                "username": "standard_user",
                "groups": ["users"]
            },
            "expected": "user"
        },
        {
            "name": "User with no groups (default viewer)",
            "user_info": {
                "username": "anonymous",
                "groups": []
            },
            "expected": "viewer"
        },
        {
            "name": "User with Keycloak realm roles",
            "user_info": {
                "username": "keycloak_admin",
                "realm_access": {
                    "roles": ["admin", "uma_authorization"]
                }
            },
            "expected": "admin"
        }
    ]

    print("Running role mapper tests...\n")
    for test in test_cases:
        result = map_keycloak_role(test["user_info"])
        status = "✓" if result == test["expected"] else "✗"
        print(f"{status} {test['name']}: expected '{test['expected']}', got '{result}'")
