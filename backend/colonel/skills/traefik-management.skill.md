---
name: traefik-management
description: View and manage Traefik routes, services, SSL certs, and middlewares
actions:
  - name: list_routers
    description: List Traefik HTTP routers
    confirmation_required: false
    parameters: {}

  - name: list_services
    description: List Traefik HTTP services
    confirmation_required: false
    parameters: {}

  - name: list_middlewares
    description: List Traefik HTTP middlewares
    confirmation_required: false
    parameters: {}

  - name: list_tls_certs
    description: List Traefik TLS certificates
    confirmation_required: false
    parameters: {}

  - name: restart_traefik
    description: Restart the Traefik container (unicorn-traefik)
    confirmation_required: true
    parameters: {}
---
Traefik management skill for the unicorn-traefik service. Uses the Traefik
API (dashboard on port 8090) to inspect routers, services, middlewares, and
TLS certificates. Restart requires confirmation.

Safety level: Medium (restart is disruptive; read-only actions are safe).

Example invocations:
- "List Traefik routers"
- "Show Traefik TLS certificates"
- "Restart Traefik"

Expected outputs:
- Tables or JSON summaries of routers/services/middlewares/certs
- Confirmation request before restart
