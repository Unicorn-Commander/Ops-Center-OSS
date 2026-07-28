---
name: git-operations
description: Git version control operations - status, diff, log, commit, branch management
actions:
  - name: status
    description: Show git status (modified files, staged changes, untracked files)
    confirmation_required: false
    parameters:
      repo_path:
        type: string
        description: Path to the git repository
        required: true

  - name: diff
    description: Show git diff of changes. Can diff staged, unstaged, or between refs.
    confirmation_required: false
    parameters:
      repo_path:
        type: string
        description: Path to the git repository
        required: true
      target:
        type: string
        description: "What to diff: 'staged', 'unstaged' (default), a branch name, or commit hash"
        default: unstaged
      file_path:
        type: string
        description: Optional specific file to diff

  - name: log
    description: Show git commit log
    confirmation_required: false
    parameters:
      repo_path:
        type: string
        description: Path to the git repository
        required: true
      count:
        type: integer
        description: Number of commits to show. Default 10.
        default: 10
      oneline:
        type: boolean
        description: Use compact one-line format. Default true.
        default: true

  - name: commit
    description: Stage files and create a git commit
    confirmation_required: true
    parameters:
      repo_path:
        type: string
        description: Path to the git repository
        required: true
      message:
        type: string
        description: Commit message
        required: true
      files:
        type: string
        description: "Space-separated list of files to stage, or '.' for all changed files"
        required: true

  - name: branch
    description: List, create, or switch branches
    confirmation_required: false
    parameters:
      repo_path:
        type: string
        description: Path to the git repository
        required: true
      action:
        type: string
        description: "'list' (default), 'create', 'checkout', or 'current'"
        default: list
        enum: [list, create, checkout, current]
      branch_name:
        type: string
        description: Branch name (required for create/checkout)

  - name: push
    description: Push commits to remote
    confirmation_required: true
    parameters:
      repo_path:
        type: string
        description: Path to the git repository
        required: true
      remote:
        type: string
        description: Remote name. Default 'origin'.
        default: origin
      branch:
        type: string
        description: Branch to push. Default is current branch.
---
Git version control operations for managing repositories on the server.
Supports all common git workflows: viewing status, diffs, logs, creating
commits, managing branches, and pushing to remotes. Destructive operations
(commit, push) require user confirmation.
