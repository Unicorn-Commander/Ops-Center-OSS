---
name: forgejo-management
description: Query Forgejo Git server for repositories and organizations
actions:
  - name: list_repos
    description: List repositories in the Forgejo Git server
    confirmation_required: false
    parameters: {}

  - name: list_orgs
    description: List organizations in Forgejo
    confirmation_required: false
    parameters: {}
---
Forgejo Git server management skill. Queries the unicorn-forgejo container
for repository and organization information. All operations are read-only.
