---
name: network-diagnostics
description: Port checks, DNS lookups, and Docker network inspection
actions:
  - name: port_check
    description: Check if a host:port is reachable
    confirmation_required: false
    parameters:
      host:
        type: string
        description: Hostname or IP to check
        required: true
      port:
        type: integer
        description: TCP port to check
        required: true
      timeout:
        type: integer
        description: Timeout in seconds
        default: 3

  - name: dns_lookup
    description: Resolve a hostname using system DNS
    confirmation_required: false
    parameters:
      hostname:
        type: string
        description: Hostname to resolve
        required: true

  - name: list_docker_networks
    description: List Docker networks
    confirmation_required: false
    parameters: {}

  - name: inspect_docker_network
    description: Inspect a Docker network
    confirmation_required: false
    parameters:
      network_name:
        type: string
        description: Docker network name
        required: true
---
Network diagnostics for UC-Cloud. Useful for validating connectivity between
services on unicorn-network and external endpoints.

Safety level: Low (read-only).

Example invocations:
- "Check if ai.magicunicorn.dev:443 is reachable"
- "Resolve auth.magicunicorn.dev"
- "Inspect docker network unicorn-network"

Expected outputs:
- Open/closed port status
- DNS records from getent/nslookup
- Docker network inspection JSON
