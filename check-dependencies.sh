#!/bin/bash
#
# UC-1 Pro Admin Dashboard - Dependency Check Script
#

echo "UC-1 Pro Admin Dashboard - Dependency Check"
echo "==========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed ($(which $1))"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        return 1
    fi
}

# Function to check Python package
check_python_package() {
    if python3 -c "import $1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Python package '$1' is installed"
        return 0
    else
        echo -e "${RED}✗${NC} Python package '$1' is NOT installed"
        return 1
    fi
}

echo "System Dependencies:"
echo "-------------------"
check_command python3
check_command pip3
check_command node
check_command npm
check_command git
check_command docker

echo ""
echo "Network Management Tools:"
echo "------------------------"
check_command netplan
check_command ip
check_command iw
check_command iwconfig
check_command ifconfig
check_command ethtool
check_command wpa_supplicant

echo ""
echo "System Monitoring Tools:"
echo "-----------------------"
check_command htop
check_command iotop
check_command iostat

echo ""
echo "Python Version:"
echo "--------------"
if command -v python3 &> /dev/null; then
    python3 --version
fi

echo ""
echo "Node.js Version:"
echo "---------------"
if command -v node &> /dev/null; then
    node --version
    npm --version
fi

echo ""
echo "Checking Backend Python Environment:"
echo "-----------------------------------"
BACKEND_DIR="$(dirname "$0")/backend"
if [ -d "$BACKEND_DIR/venv" ]; then
    echo -e "${GREEN}✓${NC} Python virtual environment exists"
    
    # Check if we can activate it
    if [ -f "$BACKEND_DIR/venv/bin/activate" ]; then
        source "$BACKEND_DIR/venv/bin/activate" 2>/dev/null
        echo "Checking installed Python packages:"
        
        # Check key packages
        for pkg in fastapi uvicorn psutil docker yaml; do
            check_python_package $pkg
        done
        
        deactivate 2>/dev/null
    fi
else
    echo -e "${YELLOW}!${NC} Python virtual environment not found at $BACKEND_DIR/venv"
    echo "  Run: cd backend && python3 -m venv venv"
fi

echo ""
echo "Checking Permissions:"
echo "--------------------"
# Check if uc1admin group exists
if getent group uc1admin > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Group 'uc1admin' exists"
    
    # Check if current user is in the group
    if groups | grep -q uc1admin; then
        echo -e "${GREEN}✓${NC} Current user is in 'uc1admin' group"
    else
        echo -e "${YELLOW}!${NC} Current user is NOT in 'uc1admin' group"
        echo "  Run: sudo usermod -a -G uc1admin $USER"
    fi
else
    echo -e "${YELLOW}!${NC} Group 'uc1admin' does not exist"
    echo "  Run: sudo groupadd uc1admin"
fi

# Check sudoers file
if [ -f "/etc/sudoers.d/uc1-admin-network" ]; then
    echo -e "${GREEN}✓${NC} Sudoers file exists for network permissions"
else
    echo -e "${YELLOW}!${NC} Sudoers file not found at /etc/sudoers.d/uc1-admin-network"
    echo "  Run the install.sh script to set up permissions"
fi

echo ""
echo "Summary:"
echo "--------"
echo "To install missing dependencies, run:"
echo -e "${YELLOW}sudo ./install.sh${NC}"
echo ""
echo "For manual installation of specific tools:"
echo "- Network tools: sudo apt-get install iw wireless-tools"
echo "- Monitoring tools: sudo apt-get install htop iotop sysstat"
echo "- Python packages: cd backend && source venv/bin/activate && pip install -r requirements.txt"