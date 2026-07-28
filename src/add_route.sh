#!/bin/bash

# Backup App.jsx
cp App.jsx App.jsx.backup

# Add import after LocalUsers (line 56)
sed -i '56 a const LocalUserManagement = lazy(() => import('\''./pages/LocalUserManagement'\''));' App.jsx

# Find the line with "system/local-users" route and add new route after it
# Line 267 has: <Route path="system/local-users" element={<LocalUsers />} />
sed -i '/path="system\/local-users"/a \                  <Route path="system/local-user-management" element={<LocalUserManagement />} />' App.jsx

echo "✅ Added LocalUserManagement route to App.jsx"
