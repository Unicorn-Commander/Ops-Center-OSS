---
name: docker-management
description: List, inspect, manage, and get logs/stats from Docker containers
actions:
  - name: list_containers
    description: List Docker containers filtered by status
    confirmation_required: false
    parameters:
      status:
        type: string
        description: Filter by container status
        enum: [running, all, exited, paused]
        default: running

  - name: inspect_container
    description: Get detailed information about a specific container including ports, networks, memory, and labels
    confirmation_required: false
    parameters:
      container_name:
        type: string
        description: Name of the Docker container
        required: true

  - name: container_logs
    description: Get recent logs from a container
    confirmation_required: false
    parameters:
      container_name:
        type: string
        description: Name of the Docker container
        required: true
      lines:
        type: integer
        description: Number of log lines to retrieve
        default: 50
      since:
        type: string
        description: Show logs since timestamp (e.g. 2024-01-01T00:00:00)

  - name: container_stats
    description: Get real-time CPU, memory, and network stats for a container
    confirmation_required: false
    parameters:
      container_name:
        type: string
        description: Name of the Docker container
        required: true

  - name: manage_container
    description: Start, stop, restart, or kill a Docker container
    confirmation_required: true
    parameters:
      container_name:
        type: string
        description: Name of the Docker container
        required: true
      action:
        type: string
        description: Action to perform
        enum: [start, stop, restart, kill]
        required: true
---
Docker container management skill. Use this to query and manage Docker containers
running on the server. Critical containers (postgresql, redis, keycloak, ops-center,
traefik) are protected from stop/kill operations.
