---
name: system-status
description: Check system health including CPU, memory, disk, GPU usage, and top processes
actions:
  - name: cpu
    description: Get CPU usage, core count, frequency, and load averages
    confirmation_required: false
    parameters: {}

  - name: memory
    description: Get RAM and swap usage details
    confirmation_required: false
    parameters: {}

  - name: disk
    description: Get disk usage for all mounted partitions
    confirmation_required: false
    parameters: {}

  - name: gpu
    description: Get GPU status including memory, temperature, and utilization via nvidia-smi
    confirmation_required: false
    parameters: {}

  - name: processes
    description: Get top processes sorted by CPU usage
    confirmation_required: false
    parameters:
      count:
        type: integer
        description: Number of top processes to show
        default: 10

  - name: full_status
    description: Get comprehensive system status (CPU + memory + disk + GPU combined)
    confirmation_required: false
    parameters: {}
---
System monitoring skill. Provides real-time metrics about the server hardware
including CPU, memory, disk, GPU, and running processes.
