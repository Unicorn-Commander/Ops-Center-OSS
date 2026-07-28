---
name: frontend-management
description: Read, edit, build, and deploy the Ops-Center frontend (React/Vite)
actions:
  - name: read_source
    description: Read a frontend source file (JSX, JS, CSS, etc.) from the ops-center src/ directory
    confirmation_required: false
    parameters:
      path:
        type: string
        description: "Relative path from the ops-center root (e.g. src/pages/admin/ColonelChat.jsx)"
        required: true
  - name: list_files
    description: List files in a directory of the frontend source tree
    confirmation_required: false
    parameters:
      path:
        type: string
        description: "Relative directory path (e.g. src/components/colonel)"
        default: "src"
  - name: edit_source
    description: Edit a frontend source file by replacing a specific string with new content
    confirmation_required: true
    parameters:
      path:
        type: string
        description: "Relative path to the file to edit"
        required: true
      old_text:
        type: string
        description: "Exact text to find and replace (must be unique in the file)"
        required: true
      new_text:
        type: string
        description: "New text to replace with"
        required: true
  - name: build_frontend
    description: Run npm build to compile the React frontend
    confirmation_required: true
    parameters: {}
  - name: deploy_frontend
    description: Copy built frontend from dist/ to public/ (makes changes live)
    confirmation_required: true
    parameters: {}
  - name: get_build_status
    description: Check if the last frontend build succeeded and show any errors
    confirmation_required: false
    parameters: {}
---
Frontend management skill for modifying the Ops-Center React/Vite application.
Allows The Colonel to read source files, make targeted edits, build, and deploy.
All edits use string replacement (not line numbers) for safety. Build and deploy
operations require user confirmation before execution.
