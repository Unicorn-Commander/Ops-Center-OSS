#!/bin/bash

# Backup server.py
cp server.py server.py.backup

# Add import for local_users_api (after line 78)
sed -i '78 a from local_users_api import router as admin_local_users_router' server.py

# Add router registration (after line 366)
sed -i '366 a app.include_router(admin_local_users_router)\nlogger.info("Admin Local User Management API endpoints registered at /api/v1/admin/system/local-users")' server.py

echo "✅ Integrated local_users_api into server.py"
