---
name: postgresql-ops
description: Query and monitor PostgreSQL databases
actions:
  - name: list_databases
    description: List all PostgreSQL databases with sizes
    confirmation_required: false
    parameters: {}

  - name: list_tables
    description: List all tables in a database with sizes
    confirmation_required: false
    parameters:
      database:
        type: string
        description: Database name
        default: unicorn_db

  - name: query
    description: "Run a SQL query. Write operations (INSERT, UPDATE, DELETE) available with write-capable models."
    confirmation_required: true
    parameters:
      query:
        type: string
        description: SQL query to execute
        required: true
      database:
        type: string
        description: Database name
        default: unicorn_db

  - name: stats
    description: Get PostgreSQL database statistics (connections, transactions)
    confirmation_required: false
    parameters: {}
---
PostgreSQL operations skill. Read operations (SELECT, EXPLAIN) always available.
Write operations (INSERT, UPDATE, DELETE) unlocked when using a write-capable model.
DROP, ALTER, and TRUNCATE are always blocked.
