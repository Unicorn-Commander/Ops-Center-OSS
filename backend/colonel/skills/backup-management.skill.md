---
name: backup-management
description: Trigger backups, list snapshots, and restore database backups
actions:
  - name: trigger_backup
    description: Run the UC-Cloud automated backup script
    confirmation_required: false
    parameters:
      backup_dir:
        type: string
        description: Optional backup directory override
      dry_run:
        type: boolean
        description: If true, do not write files
        default: false

  - name: list_backups
    description: List recent backup files
    confirmation_required: false
    parameters:
      backup_dir:
        type: string
        description: Directory to list (defaults to project backups)
      limit:
        type: integer
        description: Max number of results
        default: 10

  - name: restore_database
    description: Restore PostgreSQL from a backup file (creates safety backup first)
    confirmation_required: true
    parameters:
      backup_file:
        type: string
        description: Full path to the backup file
        required: true

  - name: cleanup_old_backups
    description: Remove old UC-Cloud backups based on retention settings
    confirmation_required: true
    parameters:
      days:
        type: integer
        description: Retention period in days
        default: 7
      keep:
        type: integer
        description: Minimum backups to keep
        default: 3
      backup_dir:
        type: string
        description: Optional backup directory override
---
Backup management skill using UC-Cloud scripts in services/ops-center/scripts.
Targets PostgreSQL (unicorn-postgresql) and Redis backups produced by
automated-backup.sh and related tooling.

Safety level: High (restore and cleanup are destructive and require confirmation).

Example invocations:
- "Trigger a backup"
- "List recent backups"
- "Restore database from /home/muut/backups/database/unicorn_db_20260101.sql"

Expected outputs:
- Backup creation summary and file paths
- Backup listings sorted by most recent
- Restore status and safety backup path
