#!/bin/bash
#
# Ops-Center Installation Script
# Installs all system dependencies for the Ops-Center dashboard
#
# Usage:
#   sudo ./install.sh              # Full install (bare metal)
#   sudo ./install.sh --docker     # Docker-only install
#   sudo ./install.sh --dev        # Development dependencies only (no root)
#
# For Docker Compose deployments (recommended):
#   docker compose -f docker-compose.direct.yml up -d
#

set -e

# ─── Colors ──────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# ─── Banner ──────────────────────────────────────────────────────────────

echo ""
echo -e "${PURPLE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                                       ║${NC}"
echo -e "${PURPLE}║       Ops-Center Installation Script v2.5.0           ║${NC}"
echo -e "${PURPLE}║       The AI-Powered Infrastructure Command Center    ║${NC}"
echo -e "${PURPLE}║                                                       ║${NC}"
echo -e "${PURPLE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Parse Arguments ─────────────────────────────────────────────────────

INSTALL_MODE="full"
while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)   INSTALL_MODE="docker"; shift ;;
        --dev)      INSTALL_MODE="dev"; shift ;;
        --help|-h)
            echo "Usage: sudo ./install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --docker    Install Docker and start services only"
            echo "  --dev       Install development dependencies only (no root needed)"
            echo "  --help      Show this help message"
            echo ""
            echo "For Docker Compose deployment (recommended):"
            echo "  docker compose -f docker-compose.direct.yml up -d"
            exit 0
            ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
    esac
done

# ─── Root Check ──────────────────────────────────────────────────────────

if [ "$EUID" -ne 0 ] && [ "$INSTALL_MODE" != "dev" ]; then
    echo -e "${RED}This script needs root privileges for system packages.${NC}"
    echo "Please run: sudo ./install.sh"
    echo ""
    echo "For development-only setup (no root needed): ./install.sh --dev"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
CURRENT_USER="${SUDO_USER:-$USER}"

# ─── Helper Functions ────────────────────────────────────────────────────

step() { echo -e "\n${BLUE}[$1/${TOTAL_STEPS}]${NC} ${GREEN}$2${NC}"; }
warn() { echo -e "  ${YELLOW}!${NC} $1"; }
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }

# ─── Count Steps ─────────────────────────────────────────────────────────

if [ "$INSTALL_MODE" = "dev" ]; then
    TOTAL_STEPS=4
elif [ "$INSTALL_MODE" = "docker" ]; then
    TOTAL_STEPS=3
else
    TOTAL_STEPS=8
fi

CURRENT_STEP=0

# ═══════════════════════════════════════════════════════════════════════════
# System Dependencies (skip for --dev)
# ═══════════════════════════════════════════════════════════════════════════

if [ "$INSTALL_MODE" != "dev" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    step $CURRENT_STEP "Installing system dependencies"

    apt-get update -qq > /dev/null 2>&1

    apt-get install -y -qq \
        python3 python3-pip python3-venv python3-dev \
        git curl wget build-essential libpq-dev \
        > /dev/null 2>&1

    ok "System packages installed"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Docker
# ═══════════════════════════════════════════════════════════════════════════

if [ "$INSTALL_MODE" != "dev" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    step $CURRENT_STEP "Setting up Docker"

    if command -v docker &> /dev/null; then
        ok "Docker already installed ($(docker --version | cut -d' ' -f3 | tr -d ','))"
    else
        curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
        sh /tmp/get-docker.sh > /dev/null 2>&1
        rm -f /tmp/get-docker.sh
        ok "Docker installed"
    fi

    if [ -n "$CURRENT_USER" ] && [ "$CURRENT_USER" != "root" ]; then
        usermod -aG docker "$CURRENT_USER" 2>/dev/null || true
        ok "Added $CURRENT_USER to docker group"
    fi

    if docker compose version &> /dev/null; then
        ok "Docker Compose plugin available"
    else
        warn "Docker Compose not found — install: https://docs.docker.com/compose/install/"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# Node.js
# ═══════════════════════════════════════════════════════════════════════════

CURRENT_STEP=$((CURRENT_STEP + 1))
step $CURRENT_STEP "Setting up Node.js"

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1 | tr -d 'v')
    if [ "$NODE_MAJOR" -ge 20 ]; then
        ok "Node.js $NODE_VERSION"
    else
        warn "Node.js $NODE_VERSION found but >=20 required"
        if [ "$EUID" -eq 0 ]; then
            curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
            apt-get install -y -qq nodejs > /dev/null 2>&1
            ok "Node.js $(node --version) installed"
        fi
    fi
else
    if [ "$EUID" -eq 0 ]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
        apt-get install -y -qq nodejs > /dev/null 2>&1
        ok "Node.js $(node --version) installed"
    else
        warn "Node.js not found — install Node.js 20+: https://nodejs.org/"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# Frontend Dependencies
# ═══════════════════════════════════════════════════════════════════════════

CURRENT_STEP=$((CURRENT_STEP + 1))
step $CURRENT_STEP "Installing frontend dependencies"

cd "$SCRIPT_DIR"
if [ -f "package.json" ]; then
    npm install --silent 2>/dev/null
    ok "npm packages installed"
else
    warn "package.json not found"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Python Backend
# ═══════════════════════════════════════════════════════════════════════════

CURRENT_STEP=$((CURRENT_STEP + 1))
step $CURRENT_STEP "Setting up Python backend"

cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    ok "Virtual environment created"
else
    ok "Virtual environment exists"
fi

source venv/bin/activate
pip install --upgrade pip -q 2>/dev/null

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q 2>/dev/null
    ok "Python dependencies installed"
else
    warn "requirements.txt not found"
fi

deactivate
cd "$SCRIPT_DIR"

# ═══════════════════════════════════════════════════════════════════════════
# Environment Configuration
# ═══════════════════════════════════════════════════════════════════════════

CURRENT_STEP=$((CURRENT_STEP + 1))
step $CURRENT_STEP "Checking environment configuration"

if [ -f ".env.auth" ]; then
    ok ".env.auth exists"
else
    if [ -f ".env.example" ]; then
        cp .env.example .env.auth
        ok "Created .env.auth from .env.example"
        warn "Edit .env.auth with your configuration: nano .env.auth"
    else
        warn "Create .env.auth from .env.example with your settings"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# Systemd Service (full install only)
# ═══════════════════════════════════════════════════════════════════════════

if [ "$INSTALL_MODE" = "full" ] && [ "$EUID" -eq 0 ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    step $CURRENT_STEP "Configuring systemd service"

    cat > /etc/systemd/system/ops-center.service << SERVICEEOF
[Unit]
Description=Ops-Center - AI Infrastructure Command Center
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$BACKEND_DIR/venv/bin/python server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ops-center

[Install]
WantedBy=multi-user.target
SERVICEEOF

    systemctl daemon-reload
    ok "systemd service created (ops-center)"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Build Frontend (full install only)
# ═══════════════════════════════════════════════════════════════════════════

if [ "$INSTALL_MODE" = "full" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    step $CURRENT_STEP "Building frontend for production"

    cd "$SCRIPT_DIR"
    if npm run build 2>/dev/null && [ -d "dist" ]; then
        cp -r dist/* public/ 2>/dev/null
        ok "Frontend built and deployed to public/"
    else
        warn "Build skipped — run manually: npm run build && cp -r dist/* public/"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# Done
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${PURPLE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Installation complete!${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════${NC}"
echo ""

if [ "$INSTALL_MODE" = "full" ]; then
    echo "  Next steps:"
    echo ""
    echo "  1. Configure your environment:"
    echo "     nano .env.auth"
    echo ""
    echo "  2. Start with Docker Compose (recommended):"
    echo "     docker compose -f docker-compose.direct.yml up -d"
    echo ""
    echo "     OR start with systemd (bare metal):"
    echo "     sudo systemctl start ops-center"
    echo "     sudo systemctl enable ops-center"
    echo ""
    echo "  3. Access the dashboard: http://localhost:8084"
    echo "  4. Set up Keycloak and create your first admin user"
    echo ""
elif [ "$INSTALL_MODE" = "docker" ]; then
    echo "  Start services:"
    echo "    docker compose -f docker-compose.direct.yml up -d"
    echo ""
    echo "  Dashboard: http://localhost:8084"
    echo ""
elif [ "$INSTALL_MODE" = "dev" ]; then
    echo "  Start development:"
    echo ""
    echo "  Backend:  cd backend && source venv/bin/activate && uvicorn server:app --reload --port 8084"
    echo "  Frontend: npm run dev"
    echo ""
    echo "  Dashboard: http://localhost:5173 (dev) / http://localhost:8084 (backend)"
    echo ""
fi

if [ -n "$CURRENT_USER" ] && [ "$CURRENT_USER" != "root" ] && [ "$INSTALL_MODE" != "dev" ]; then
    echo -e "  ${YELLOW}Note:${NC} Log out and back in for Docker group permissions."
    echo ""
fi
