---
name: bash-execution
description: Run shell commands on the server with safety validation and timeout
actions:
  - name: run_command
    description: Execute a bash command and return the output. Dangerous commands are blocked.
    confirmation_required: false
    parameters:
      command:
        type: string
        description: The bash command to execute
        required: true
      timeout:
        type: integer
        description: Timeout in seconds (max 60)
        default: 30
---
Bash command execution with safety validation. Commands are validated against
a blocklist of dangerous patterns before execution. Output is sanitized to
remove ANSI codes and redact sensitive values (passwords, tokens, API keys).
Commands that modify services require user confirmation.
