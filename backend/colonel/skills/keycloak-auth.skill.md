---
name: keycloak-auth
description: Query Keycloak authentication server for users and realm information
actions:
  - name: list_users
    description: List users in the uchub Keycloak realm
    confirmation_required: false
    parameters: {}

  - name: list_realms
    description: List all Keycloak realms
    confirmation_required: false
    parameters: {}

  - name: user_info
    description: Get detailed information about a specific user
    confirmation_required: false
    parameters:
      username:
        type: string
        description: Username to look up
        required: true
---
Keycloak authentication skill. Queries the uchub-keycloak container for user
and realm information. All operations are read-only.
