# Ops-Center Build Requirements

**Last Updated**: October 30, 2025
**Version**: 2.1.1
**Purpose**: Complete guide for building Ops-Center frontend on any system

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Required Software](#required-software)
3. [Build Order](#build-order)
4. [Common Build Errors](#common-build-errors)
5. [Environment Variables](#environment-variables)
6. [Troubleshooting](#troubleshooting)
7. [Build Verification](#build-verification)

---

## System Requirements

### Minimum Requirements

- **Operating System**: Linux, macOS, or Windows 10/11 with WSL2
- **RAM**: 4GB available memory (8GB recommended)
- **Disk Space**: 2GB free space for dependencies and build output
- **CPU**: Multi-core processor (2+ cores recommended)

### Recommended Requirements

- **RAM**: 8GB+ available memory
- **Disk Space**: 5GB+ free space
- **CPU**: 4+ cores for faster builds
- **Internet**: Stable broadband connection (for npm packages)

---

## Required Software

### 1. Node.js

**Minimum Version**: v18.0.0
**Recommended Version**: v20.0.0+
**Current Production Version**: v22.19.0

**Installation**:

```bash
# Using nvm (recommended)
nvm install 22.19.0
nvm use 22.19.0

# Or download from: https://nodejs.org/
```

**Verification**:

```bash
node --version
# Expected output: v22.19.0 (or higher)
```

### 2. npm

**Minimum Version**: v9.0.0
**Recommended Version**: v10.0.0+
**Current Production Version**: v10.9.3

**Installation** (if not included with Node.js):

```bash
npm install -g npm@latest
```

**Verification**:

```bash
npm --version
# Expected output: 10.9.3 (or higher)
```

### 3. Git

**Required for**: Cloning repository, submodule management

**Installation**:

```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git

# Windows
# Download from: https://git-scm.com/
```

---

## Build Order

The Ops-Center build process has **three distinct phases** that must be executed in order:

### Phase 1: Backend Preparation

**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/`

The backend doesn't need building (Python), but ensure all dependencies are installed:

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Install Python dependencies (inside Docker container)
docker exec ops-center-direct pip install -r /app/requirements.txt
```

**Critical Backend Files**:
- `backend/server.py` - Main FastAPI application
- `backend/requirements.txt` - Python dependencies
- `backend/*.py` - API endpoint modules

### Phase 2: Frontend Build

**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/`

This is the **critical phase** where build errors typically occur.

#### Step 1: Verify Dependencies

```bash
# Run verification script BEFORE building
./scripts/verify-build-deps.sh

# If issues detected, run with --fix
./scripts/verify-build-deps.sh --fix
```

#### Step 2: Install npm Packages

```bash
# Clean install (recommended for fresh systems)
rm -rf node_modules package-lock.json
npm install

# Or regular install
npm install
```

**Expected Duration**: 2-5 minutes (depending on internet speed)

#### Step 3: Build Frontend

```bash
# Production build
npm run build

# If build runs out of memory, use:
NODE_OPTIONS='--max-old-space-size=4096' npm run build
```

**Expected Output**:
```
✓ 1234 modules transformed.
dist/index.html                    5.67 kB │ gzip:  2.13 kB
dist/assets/index-BPkI3YZ-.js     245.32 kB │ gzip: 89.45 kB
dist/assets/index-CUWEzy24.css     12.89 kB │ gzip:  3.21 kB
✓ built in 45.23s
```

**Expected Duration**: 30-90 seconds (depending on system)

#### Step 4: Deploy to public/

```bash
# Copy built files to public directory (served by Nginx)
cp -r dist/* public/
```

**Verification**:
```bash
ls -lh public/index.html public/assets/
# Should show index.html and assets/ directory with .js and .css files
```

### Phase 3: Docker Deployment

**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/`

#### Step 1: Restart Container

```bash
# Restart to load new frontend files
docker restart ops-center-direct

# Wait for startup
sleep 5

# Verify container is running
docker ps | grep ops-center
```

#### Step 2: Test Deployment

```bash
# Test backend API
curl http://localhost:8084/api/v1/system/status

# Access frontend
# Navigate to: https://your-domain.com/admin
```

---

## Common Build Errors

### Error 1: "Module not found: SubscriptionManagement"

**Symptom**:
```
ERROR in ./src/App.jsx
Module not found: Can't resolve './pages/admin/SubscriptionManagement'
```

**Root Cause**: Component file missing or incorrect import path

**Solution**:
```bash
# Verify file exists
ls -l src/pages/admin/SubscriptionManagement.jsx

# Check import statement in src/App.jsx
grep "SubscriptionManagement" src/App.jsx

# Should show:
# const SubscriptionManagement = lazy(() => import('./pages/admin/SubscriptionManagement'));
```

**Fix** (if file missing):
```bash
# File should exist at:
# /home/muut/Production/UC-Cloud/services/ops-center/src/pages/admin/SubscriptionManagement.jsx

# If missing, restore from git:
git checkout src/pages/admin/SubscriptionManagement.jsx
```

### Error 2: "Cannot find module 'react'"

**Symptom**:
```
Error: Cannot find module 'react'
```

**Root Cause**: node_modules not installed or corrupted

**Solution**:
```bash
# Remove and reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Error 3: "JavaScript heap out of memory"

**Symptom**:
```
FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory
```

**Root Cause**: Insufficient memory allocated to Node.js

**Solution**:
```bash
# Increase Node.js memory limit
NODE_OPTIONS='--max-old-space-size=4096' npm run build

# Or add to package.json:
# "build": "NODE_OPTIONS='--max-old-space-size=4096' vite build"
```

### Error 4: "Peer dependency warnings"

**Symptom**:
```
npm WARN ERESOLVE overriding peer dependency
npm WARN ERESOLVE conflicting peerDependency: react@^17.0.0
```

**Root Cause**: Dependency version conflicts

**Solution**:
```bash
# Install with legacy peer deps flag
npm install --legacy-peer-deps

# Or force (less recommended)
npm install --force
```

### Error 5: "EACCES: permission denied"

**Symptom**:
```
Error: EACCES: permission denied, mkdir '/home/user/.npm'
```

**Root Cause**: Incorrect npm permissions

**Solution**:
```bash
# Fix npm permissions
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) /usr/local/lib/node_modules

# Or use nvm instead of global npm
```

### Error 6: "Vite config error"

**Symptom**:
```
Error: Failed to load config from vite.config.js
```

**Root Cause**: Invalid vite.config.js or missing plugins

**Solution**:
```bash
# Verify vite.config.js exists
ls -l vite.config.js

# Check for @vitejs/plugin-react
grep "plugin-react" vite.config.js

# Reinstall Vite plugin
npm install --save-dev @vitejs/plugin-react
```

### Error 7: "Circular dependency detected"

**Symptom**:
```
Circular dependency: src/contexts/SystemContext.jsx -> src/contexts/OrganizationContext.jsx -> src/contexts/SystemContext.jsx
```

**Root Cause**: Circular import between context providers

**Solution**:
```bash
# This is a known architecture pattern in Ops-Center
# It's handled correctly at runtime
# Build should still succeed - if not, check for:

# 1. Direct circular imports (not via lazy loading)
grep -r "import.*SystemContext" src/contexts/
grep -r "import.*OrganizationContext" src/contexts/

# 2. Missing React.lazy() wrapper
grep -r "lazy(() => import" src/App.jsx
```

### Error 8: "dist/ directory empty after build"

**Symptom**: Build completes but dist/ is empty or missing files

**Root Cause**: Build cache corruption or Vite config issue

**Solution**:
```bash
# Clear build cache
rm -rf dist/ node_modules/.vite

# Rebuild
npm run build

# Verify output
ls -lh dist/
```

---

## Environment Variables

### Required Variables

These variables are loaded from `.env.auth` (backend) and used during runtime (not build):

```bash
# Keycloak SSO
KEYCLOAK_URL=http://uchub-keycloak:8080
KEYCLOAK_REALM=uchub
KEYCLOAK_CLIENT_ID=ops-center
KEYCLOAK_CLIENT_SECRET=<secret>

# Database
POSTGRES_HOST=unicorn-postgresql
POSTGRES_DB=unicorn_db

# Redis
REDIS_HOST=unicorn-redis
```

### Optional Build Variables

```bash
# Node.js memory limit
NODE_OPTIONS='--max-old-space-size=4096'

# Vite build mode
NODE_ENV=production
```

**Note**: Frontend build does NOT require environment variables. All API endpoints are configured at runtime via Vite's proxy configuration.

---

## Troubleshooting

### Build Verification Checklist

Before reporting build issues, verify:

- [ ] Node.js version >= 18.0.0 (`node --version`)
- [ ] npm version >= 9.0.0 (`npm --version`)
- [ ] package.json exists and is valid JSON
- [ ] node_modules directory exists (`ls node_modules/react`)
- [ ] src/pages/admin/SubscriptionManagement.jsx exists
- [ ] vite.config.js exists and has React plugin
- [ ] At least 4GB RAM available
- [ ] At least 2GB disk space free

### Automated Verification

```bash
# Run comprehensive verification
./scripts/verify-build-deps.sh

# Attempt automatic fixes
./scripts/verify-build-deps.sh --fix
```

### Clean Build Process

If all else fails, perform a complete clean build:

```bash
# Step 1: Remove all build artifacts
rm -rf node_modules dist public/assets package-lock.json
rm -rf node_modules/.vite

# Step 2: Clear npm cache
npm cache clean --force

# Step 3: Verify Node.js/npm
node --version  # Should be v18.0.0+
npm --version   # Should be v9.0.0+

# Step 4: Fresh install
npm install

# Step 5: Build
npm run build

# Step 6: Deploy
cp -r dist/* public/

# Step 7: Restart
docker restart ops-center-direct
```

### Getting Help

If build still fails after following this guide:

1. **Run verification script**:
   ```bash
   ./scripts/verify-build-deps.sh > build-verification-report.txt 2>&1
   ```

2. **Capture build output**:
   ```bash
   npm run build > build-output.txt 2>&1
   ```

3. **System information**:
   ```bash
   node --version > system-info.txt
   npm --version >> system-info.txt
   cat /proc/meminfo | grep MemAvailable >> system-info.txt
   df -h >> system-info.txt
   ```

4. **Provide all three files** when requesting assistance

---

## Build Verification

### Post-Build Verification

After successful build, verify these artifacts exist:

```bash
# Critical files
ls -lh dist/index.html
ls -lh public/index.html
ls -lh public/assets/index-*.js
ls -lh public/assets/index-*.css

# Component chunks (should include SubscriptionManagement)
ls -lh dist/assets/ | grep SubscriptionManagement

# Frontend accessible
curl -I http://localhost:8084/ | grep "200 OK"
```

### Expected Build Artifacts

```
dist/
├── index.html (5-10 KB)
└── assets/
    ├── index-{hash}.js (200-300 KB)
    ├── index-{hash}.css (10-20 KB)
    ├── SubscriptionManagement-{hash}.js (50-100 KB)
    ├── UserManagement-{hash}.js (40-80 KB)
    └── ... (other lazy-loaded components)

public/
├── index.html (copied from dist/)
└── assets/ (copied from dist/)
```

### Runtime Verification

```bash
# Backend API responding
curl http://localhost:8084/api/v1/system/status

# Frontend loads
curl -I http://localhost:8084/

# Check Docker logs for errors
docker logs ops-center-direct --tail 50
```

---

## Quick Reference

### One-Command Build

```bash
# Complete build and deploy
npm install && npm run build && cp -r dist/* public/ && docker restart ops-center-direct
```

### Development Mode

```bash
# Run Vite dev server (hot reload)
npm run dev
# Access at: http://localhost:5173
```

### Build Statistics

```bash
# Generate build report
npm run build -- --mode=report

# Analyze bundle size
npx vite-bundle-visualizer
```

---

## Related Documentation

- **UC-Cloud Main**: `/home/muut/Production/UC-Cloud/CLAUDE.md`
- **Ops-Center CLAUDE.md**: `/home/muut/Production/UC-Cloud/services/ops-center/CLAUDE.md`
- **Docker Compose**: `docker-compose.direct.yml`
- **Vite Config**: `vite.config.js`
- **Package Manifest**: `package.json`

---

## Changelog

### 2025-10-30
- Created comprehensive build requirements documentation
- Added build verification script
- Documented SubscriptionManagement component build issue
- Added troubleshooting for fresh system builds
- Included automated verification tooling

---

**Remember**: Always run `./scripts/verify-build-deps.sh` before building to catch issues early!
