---
name: file-operations
description: Read, write, edit, search, and list files anywhere on the server filesystem
actions:
  - name: read_file
    description: Read a file and return its contents. Supports offset and limit for large files.
    confirmation_required: false
    parameters:
      path:
        type: string
        description: Absolute path to the file to read
        required: true
      offset:
        type: integer
        description: Line number to start reading from (1-based). Default 1.
        default: 1
      limit:
        type: integer
        description: Maximum number of lines to return. Default 200.
        default: 200

  - name: write_file
    description: Write content to a file, creating it if it doesn't exist or overwriting if it does. Use edit_file for surgical replacements.
    confirmation_required: true
    parameters:
      path:
        type: string
        description: Absolute path to the file to write
        required: true
      content:
        type: string
        description: The full content to write to the file
        required: true

  - name: edit_file
    description: Edit a file by replacing an exact string match. The old_text must appear exactly once in the file.
    confirmation_required: false
    parameters:
      path:
        type: string
        description: Absolute path to the file to edit
        required: true
      old_text:
        type: string
        description: The exact text to find and replace (must be unique in the file)
        required: true
      new_text:
        type: string
        description: The text to replace old_text with
        required: true

  - name: list_directory
    description: List files and directories at a path. Supports glob patterns like '**/*.py'.
    confirmation_required: false
    parameters:
      path:
        type: string
        description: Directory path to list, or a glob pattern like '/home/muut/project/**/*.jsx'
        required: true
      pattern:
        type: string
        description: Optional glob pattern to filter results (e.g. '*.py', '**/*.ts')

  - name: search_content
    description: Search file contents using a regex pattern (like grep/ripgrep). Returns matching lines with file paths and line numbers.
    confirmation_required: false
    parameters:
      pattern:
        type: string
        description: Regex pattern to search for
        required: true
      path:
        type: string
        description: File or directory to search in
        required: true
      file_pattern:
        type: string
        description: Glob to filter which files to search (e.g. '*.py', '*.jsx')
      max_results:
        type: integer
        description: Maximum number of matching lines to return. Default 50.
        default: 50
---
General filesystem operations for reading, writing, editing, searching, and listing files
anywhere on the server. Path validation prevents access to sensitive files like /etc/shadow
and .env files containing secrets. Write operations require a write-capable model.
