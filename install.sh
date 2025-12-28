#!/bin/bash
#
# UC-1 Pro Admin Dashboard Installation Script
# This script installs all system dependencies required for the admin dashboard
#

set -e  # Exit on error

echo "UC-1 Pro Admin Dashboard - System Dependencies Installation"
echo "=========================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "This script needs to be run with sudo privileges."
    echo "Please run: sudo ./install.sh"
    exit 1
fi

# Update package list
echo "Updating package list..."
apt-get update

# Install system dependencies
echo "Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    build-essential \
    python3-dev

# Install network management tools
echo "Installing network management tools..."
apt-get install -y \
    iw \
    wireless-tools \
    net-tools \
    ethtool \
    wpasupplicant

# Install system monitoring tools
echo "Installing system monitoring tools..."
apt-get install -y \
    htop \
    iotop \
    sysstat

# Install Docker (if not already installed)
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker is already installed"
fi

# Create virtual environment for backend
echo "Setting up Python virtual environment..."
BACKEND_DIR="$(dirname "$0")/backend"
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install Python dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Install frontend dependencies
echo "Installing frontend dependencies..."
FRONTEND_DIR="$(dirname "$0")"
cd "$FRONTEND_DIR"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt-get install -y nodejs
else
    echo "Node.js is already installed"
fi

# Install npm dependencies
echo "Installing npm dependencies..."
npm install

# Set up permissions for network management
echo "Setting up network permissions..."

# Create sudoers file for network commands
cat > /etc/sudoers.d/uc1-admin-network << EOF
# UC-1 Admin Dashboard network permissions
# Allow the admin dashboard to manage network without password
%uc1admin ALL=(ALL) NOPASSWD: /usr/sbin/netplan
%uc1admin ALL=(ALL) NOPASSWD: /usr/sbin/ip
%uc1admin ALL=(ALL) NOPASSWD: /usr/sbin/iw
%uc1admin ALL=(ALL) NOPASSWD: /usr/bin/systemctl status bluetooth
%uc1admin ALL=(ALL) NOPASSWD: /usr/bin/bluetoothctl
EOF

# Create group if it doesn't exist
if ! getent group uc1admin > /dev/null 2>&1; then
    groupadd uc1admin
    echo "Created uc1admin group"
fi

# Add current user to the group
CURRENT_USER="${SUDO_USER:-$USER}"
if [ ! -z "$CURRENT_USER" ] && [ "$CURRENT_USER" != "root" ]; then
    usermod -a -G uc1admin "$CURRENT_USER"
    echo "Added $CURRENT_USER to uc1admin group"
    echo "NOTE: You may need to log out and back in for group changes to take effect"
fi

# Create systemd service file
echo "Creating systemd service..."
cat > /etc/systemd/system/uc1-admin-dashboard.service << EOF
[Unit]
Description=UC-1 Pro Admin Dashboard
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$CURRENT_USER
Group=uc1admin
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$BACKEND_DIR/venv/bin/python server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/uc1-admin-dashboard.log
StandardError=append:/var/log/uc1-admin-dashboard.log

[Install]
WantedBy=multi-user.target
EOF

# Create log file with proper permissions
touch /var/log/uc1-admin-dashboard.log
chown $CURRENT_USER:uc1admin /var/log/uc1-admin-dashboard.log

# Reload systemd
systemctl daemon-reload

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Log out and back in for group permissions to take effect"
echo "2. Start the backend service:"
echo "   sudo systemctl start uc1-admin-dashboard"
echo "   sudo systemctl enable uc1-admin-dashboard  # To start on boot"
echo ""
echo "3. Start the frontend development server:"
echo "   cd $(dirname "$0")"
echo "   npm run dev"
echo ""
echo "4. For production, build the frontend:"
echo "   npm run build"
echo ""
echo "The admin dashboard will be available at http://localhost:8084"