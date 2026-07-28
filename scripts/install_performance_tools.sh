#!/bin/bash
# ============================================================================
# Performance Tools Installation Script
# ============================================================================
# Installs all necessary tools for performance testing and optimization
#
# Usage: ./install_performance_tools.sh
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Performance Tools Installation for Ops-Center           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# Check Prerequisites
# ============================================================================

echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}"
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}✗ pip3 not found. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y python3-pip
else
    echo -e "${GREEN}✓ pip3 found${NC}"
fi

echo ""

# ============================================================================
# Install Python Dependencies
# ============================================================================

echo -e "${YELLOW}Installing Python dependencies...${NC}"

pip3 install --upgrade pip

# Load testing tools
pip3 install locust

# Async HTTP client
pip3 install httpx[http2]

# Redis async client
pip3 install redis[hiredis]

# PostgreSQL async client
pip3 install asyncpg

# Statistics and analysis
pip3 install numpy scipy pandas

echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# ============================================================================
# Install k6
# ============================================================================

echo -e "${YELLOW}Installing k6 load testing tool...${NC}"

if command -v k6 &> /dev/null; then
    echo -e "${GREEN}✓ k6 already installed: $(k6 version)${NC}"
else
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        echo -e "${BLUE}Detected Debian/Ubuntu${NC}"

        sudo gpg -k || true
        sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
          --keyserver hkp://keyserver.ubuntu.com:80 \
          --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69

        echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
          sudo tee /etc/apt/sources.list.d/k6.list

        sudo apt-get update
        sudo apt-get install -y k6

        echo -e "${GREEN}✓ k6 installed: $(k6 version)${NC}"
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS
        echo -e "${BLUE}Detected RHEL/CentOS${NC}"

        sudo dnf install https://dl.k6.io/rpm/repo.rpm -y
        sudo dnf install k6 -y

        echo -e "${GREEN}✓ k6 installed: $(k6 version)${NC}"
    else
        echo -e "${RED}✗ Unsupported OS. Please install k6 manually:${NC}"
        echo -e "  https://k6.io/docs/getting-started/installation/"
    fi
fi

echo ""

# ============================================================================
# Install PostgreSQL Client Tools
# ============================================================================

echo -e "${YELLOW}Installing PostgreSQL client tools...${NC}"

if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL client already installed${NC}"
else
    if [ -f /etc/debian_version ]; then
        sudo apt-get install -y postgresql-client
    elif [ -f /etc/redhat-release ]; then
        sudo dnf install -y postgresql
    fi
    echo -e "${GREEN}✓ PostgreSQL client installed${NC}"
fi

echo ""

# ============================================================================
# Install Redis CLI
# ============================================================================

echo -e "${YELLOW}Installing Redis CLI...${NC}"

if command -v redis-cli &> /dev/null; then
    echo -e "${GREEN}✓ Redis CLI already installed${NC}"
else
    if [ -f /etc/debian_version ]; then
        sudo apt-get install -y redis-tools
    elif [ -f /etc/redhat-release ]; then
        sudo dnf install -y redis
    fi
    echo -e "${GREEN}✓ Redis CLI installed${NC}"
fi

echo ""

# ============================================================================
# Install Monitoring Tools
# ============================================================================

echo -e "${YELLOW}Installing monitoring tools...${NC}"

# htop for process monitoring
if ! command -v htop &> /dev/null; then
    sudo apt-get install -y htop 2>/dev/null || sudo dnf install -y htop 2>/dev/null || true
fi

# iotop for I/O monitoring
if ! command -v iotop &> /dev/null; then
    sudo apt-get install -y iotop 2>/dev/null || sudo dnf install -y iotop 2>/dev/null || true
fi

# nethogs for network monitoring
if ! command -v nethogs &> /dev/null; then
    sudo apt-get install -y nethogs 2>/dev/null || sudo dnf install -y nethogs 2>/dev/null || true
fi

echo -e "${GREEN}✓ Monitoring tools installed${NC}"
echo ""

# ============================================================================
# Create Directory Structure
# ============================================================================

echo -e "${YELLOW}Creating directory structure...${NC}"

mkdir -p tests/load/results
mkdir -p tests/performance
mkdir -p backend/cache
mkdir -p docs

echo -e "${GREEN}✓ Directory structure created${NC}"
echo ""

# ============================================================================
# Verify Installation
# ============================================================================

echo -e "${YELLOW}Verifying installation...${NC}"
echo ""

# Python packages
python3 -c "import locust; print(f'  ✓ Locust {locust.__version__}')"
python3 -c "import httpx; print(f'  ✓ httpx {httpx.__version__}')"
python3 -c "import redis; print('  ✓ redis (async)')"
python3 -c "import asyncpg; print('  ✓ asyncpg')"

# k6
if command -v k6 &> /dev/null; then
    echo -e "  ${GREEN}✓ k6 $(k6 version --quiet)${NC}"
fi

# PostgreSQL client
if command -v psql &> /dev/null; then
    echo -e "  ${GREEN}✓ psql $(psql --version | grep -oP '\d+\.\d+')${NC}"
fi

# Redis CLI
if command -v redis-cli &> /dev/null; then
    echo -e "  ${GREEN}✓ redis-cli $(redis-cli --version | grep -oP 'v=\K[^ ]+')${NC}"
fi

echo ""

# ============================================================================
# Success Message
# ============================================================================

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Installation Complete! 🚀                        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}All performance tools have been installed successfully!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Apply database indexes:"
echo "     docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /app/migrations/performance_indexes.sql"
echo ""
echo "  2. Run baseline benchmark:"
echo "     python tests/performance/benchmark.py --endpoint all --output baseline.json"
echo ""
echo "  3. Run load tests:"
echo "     ./tests/load/run_load_tests.sh --tool both --duration 300"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  - Performance Report: docs/PERFORMANCE_REPORT.md"
echo "  - Load Testing Guide: tests/load/README.md"
echo ""
