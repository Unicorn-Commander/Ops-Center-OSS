---
name: gpu-monitoring
description: Detailed NVIDIA GPU monitoring (nvidia-smi) for VRAM, temperature, and processes
actions:
  - name: summary
    description: Show GPU summary (name, memory, utilization, temperature)
    confirmation_required: false
    parameters: {}

  - name: vram_usage
    description: Show VRAM usage per GPU
    confirmation_required: false
    parameters: {}

  - name: temperatures
    description: Show GPU temperatures
    confirmation_required: false
    parameters: {}

  - name: process_list
    description: Show GPU process list
    confirmation_required: false
    parameters: {}
---
GPU monitoring skill for systems with NVIDIA GPUs (2x Tesla P40 expected).
Uses nvidia-smi for real-time utilization, VRAM, temperature, and processes.

Safety level: Low (read-only).

Example invocations:
- "Show GPU summary"
- "List GPU processes"
- "What is VRAM usage?"

Expected outputs:
- nvidia-smi summaries with per-GPU memory and utilization
- Process list with PID, process name, and VRAM usage
