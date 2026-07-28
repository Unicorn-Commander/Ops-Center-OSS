---
name: resource-cleanup
description: Docker prune, log cleanup, and disk space recovery
actions:
  - name: disk_usage
    description: Show disk usage summary
    confirmation_required: false
    parameters: {}

  - name: docker_prune
    description: Remove unused Docker resources (containers, networks, images, cache)
    confirmation_required: true
    parameters:
      include_volumes:
        type: boolean
        description: Also prune unused volumes
        default: false

  - name: cleanup_logs
    description: Truncate oversized log files under services/ops-center
    confirmation_required: true
    parameters:
      max_size_mb:
        type: integer
        description: Truncate logs larger than this size (MB)
        default: 50
---
Resource cleanup skill for reclaiming disk space on the Ops-Center host.
Targets Docker resources and local service logs.

Safety level: Medium (cleanup actions are destructive and require confirmation).

Example invocations:
- "Show disk usage"
- "Prune unused Docker resources"
- "Cleanup logs larger than 100MB"

Expected outputs:
- df/du summaries
- Docker prune results
- List of truncated log files
