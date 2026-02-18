---
name: log-viewer
description: View and search Docker container logs
actions:
  - name: get_logs
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

  - name: search_logs
    description: Search container logs for a specific pattern
    confirmation_required: false
    parameters:
      container_name:
        type: string
        description: Name of the Docker container
        required: true
      pattern:
        type: string
        description: Text pattern to search for (case-insensitive)
        required: true
      lines:
        type: integer
        description: Maximum number of matching lines to return
        default: 50
---
Log viewing and search skill. Retrieve and search through Docker container logs.
Sensitive values in log output are automatically redacted.
