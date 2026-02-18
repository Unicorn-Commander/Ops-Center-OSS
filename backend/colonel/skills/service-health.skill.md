---
name: service-health
description: Check the health status of all services or a specific service
actions:
  - name: check_all
    description: Check health status of all running Docker containers
    confirmation_required: false
    parameters: {}

  - name: check_one
    description: Check health status of a specific service/container
    confirmation_required: false
    parameters:
      service_name:
        type: string
        description: Name of the service/container to check
        required: true
---
Service health monitoring skill. Checks Docker container health status,
including detailed health check logs for containers that have health checks configured.
