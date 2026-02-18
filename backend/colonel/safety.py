"""
Safety module for Colonel skill execution.

Validates commands against blocked patterns, requires confirmation for
dangerous operations, and sanitizes output.
"""

import fnmatch
import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger("colonel.safety")

# Commands that are ALWAYS blocked (never executed)
BLOCKED_PATTERNS = [
    r"\brm\s+(-rf?\s+)?/\s*$",          # rm -rf /
    r"\brm\s+(-rf?\s+)?/\*",             # rm -rf /*
    r"\bmkfs\b",                          # Format filesystem
    r"\bdd\s+.*of=/dev/",                 # dd to device
    r":(){.*};:",                           # Fork bomb
    r"\bshutdown\b",                       # System shutdown
    r"\breboot\b",                         # System reboot
    r"\binit\s+0\b",                       # Halt system
    r"\bpoweroff\b",                       # Power off
    r">\s*/dev/sd",                        # Overwrite disk
    r"\bchmod\s+777\s+/",                  # Chmod 777 on root
    r"\bchown\s+.*\s+/\s*$",              # Chown root
    r"DROP\s+DATABASE",                    # Drop database (SQL)
    r"DROP\s+TABLE.*CASCADE",              # Drop all tables
    r"TRUNCATE\s+TABLE",                   # Truncate tables
    r"\bcurl\b.*\|\s*(ba)?sh",             # Pipe curl to shell
    r"\bwget\b.*\|\s*(ba)?sh",             # Pipe wget to shell
    r"python.*-c.*import\s+os.*system",    # Python OS command injection
    r"\biptables\s+(-F|--flush)",          # Flush firewall
    r"docker\s+system\s+prune\s+-a",       # Docker prune all
]

# Commands that require user confirmation before execution
CONFIRMATION_PATTERNS = [
    (r"\bdocker\s+(stop|kill|rm|restart)", "This will affect a running container"),
    (r"\bdocker\s+compose\s+(down|stop|restart)", "This will affect multiple containers"),
    (r"\bsystemctl\s+(stop|restart|disable)", "This will affect a system service"),
    (r"\bkill\b", "This will terminate a process"),
    (r"\bapt\s+(remove|purge|autoremove)", "This will remove packages"),
    (r"\bpip\s+uninstall\b", "This will uninstall Python packages"),
    (r"\bnpm\s+uninstall\b", "This will uninstall npm packages"),
    (r"DELETE\s+FROM", "This will delete database records"),
    (r"UPDATE\s+", "This will modify database records"),
    (r"ALTER\s+TABLE", "This will modify database schema"),
]

# Patterns to redact from command output
REDACT_PATTERNS = [
    (r'(?i)(password|passwd|secret|token|api[_-]?key|bearer)\s*[=:]\s*\S+', r'\1=<REDACTED>'),
    (r'(?i)(Authorization:\s*Bearer\s+)\S+', r'\1<REDACTED>'),
    (r'sk[_-]test[_-]\S+', '<STRIPE_KEY_REDACTED>'),
    (r'sk[_-]live[_-]\S+', '<STRIPE_KEY_REDACTED>'),
    (r'pk[_-]test[_-]\S+', '<STRIPE_KEY_REDACTED>'),
    (r'whsec_\S+', '<WEBHOOK_SECRET_REDACTED>'),
    (r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', lambda m: m.group() if len(m.group()) <= 36 else '<UUID_REDACTED>'),
]

# ANSI escape code pattern
ANSI_PATTERN = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')


def validate_command(command: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a command against safety rules.

    Returns:
        (allowed, reason): If not allowed, reason explains why.
    """
    cmd_lower = command.strip().lower()

    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return (False, f"Blocked: Command matches dangerous pattern ({pattern})")

    return (True, None)


def requires_confirmation(command: str) -> Optional[str]:
    """
    Check if a command requires user confirmation.

    Returns:
        Description of the risk if confirmation is needed, None otherwise.
    """
    for pattern, description in CONFIRMATION_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return description
    return None


def sanitize_output(output: str, max_length: int = 8000) -> str:
    """
    Sanitize command output by:
    1. Stripping ANSI escape codes
    2. Redacting sensitive values
    3. Truncating to max length
    """
    # Strip ANSI codes
    result = ANSI_PATTERN.sub('', output)

    # Redact sensitive patterns
    for pattern, replacement in REDACT_PATTERNS:
        if callable(replacement):
            result = re.sub(pattern, replacement, result)
        else:
            result = re.sub(pattern, replacement, result)

    # Truncate if too long
    if len(result) > max_length:
        truncated = result[:max_length]
        result = truncated + f"\n\n... (output truncated, {len(output)} total chars)"

    return result


def validate_docker_command(container_name: str, action: str) -> Tuple[bool, Optional[str]]:
    """Validate a Docker container operation."""
    # Protect critical containers from stop/rm
    protected = ["unicorn-postgresql", "unicorn-redis", "unicorn-keycloak", "ops-center-direct", "traefik"]

    if action in ("stop", "kill", "rm", "remove") and container_name in protected:
        return (False, f"Container '{container_name}' is a critical service and cannot be {action}ped")

    return (True, None)


def is_write_capable_model(model: str, patterns: List[str]) -> bool:
    """Check if the current model matches any write-capable pattern."""
    for pattern in patterns:
        if fnmatch.fnmatch(model.lower(), pattern.lower()):
            return True
    return False
