# UC-1 Pro Admin Dashboard Dependencies

This document lists all dependencies required for the UC-1 Pro Admin Dashboard.

## System Dependencies (Ubuntu Server 24.04)

### Core Requirements
- **Python 3.11+** - Backend runtime
- **Node.js 18+ & npm** - Frontend build tools
- **Git** - Version control
- **Build tools** - `build-essential`, `python3-dev`

### Network Management Tools
- **iw** - WiFi scanning and management
- **wireless-tools** - Additional WiFi utilities
- **net-tools** - Network utilities (ifconfig, route, etc.)
- **ethtool** - Ethernet device control
- **wpasupplicant** - WiFi authentication

### System Monitoring Tools
- **htop** - Interactive process viewer
- **iotop** - I/O monitoring
- **sysstat** - System performance tools

### Container Management
- **Docker** - Container runtime
- **Docker Compose** - Container orchestration

## Python Dependencies (Backend)

Listed in `backend/requirements.txt`:
```
fastapi==0.110.0          # Web framework
uvicorn==0.27.1           # ASGI server
websockets==12.0          # WebSocket support
aiofiles==24.1.0          # Async file operations
psutil==5.9.8             # System monitoring
docker==7.0.0             # Docker API client
gputil==1.4.0             # GPU monitoring
pydantic==2.6.1           # Data validation
python-multipart==0.0.9   # File uploads
python-dateutil==2.8.2    # Date utilities
httpx==0.27.0             # HTTP client
pyyaml==6.0.1             # YAML parsing (for netplan)
```

## Frontend Dependencies

Listed in `package.json`:
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0",
    "framer-motion": "^11.15.0",
    "recharts": "^2.15.4",
    "@heroicons/react": "^2.2.0",
    "axios": "^1.7.9"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "vite": "^5.4.19",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.5.2",
    "autoprefixer": "^10.4.20",
    "@types/react": "^18.3.17",
    "@types/react-dom": "^18.3.5"
  }
}
```

## Installation

### Quick Install (Recommended)
```bash
# Run the installation script with sudo
sudo ./install.sh
```

### Manual Installation

#### 1. System Dependencies
```bash
# Update package list
sudo apt-get update

# Install Python and build tools
sudo apt-get install -y python3 python3-pip python3-venv git curl build-essential python3-dev

# Install network tools
sudo apt-get install -y iw wireless-tools net-tools ethtool wpasupplicant

# Install monitoring tools
sudo apt-get install -y htop iotop sysstat

# Install Docker (if needed)
curl -fsSL https://get.docker.com | sudo sh
```

#### 2. Node.js Installation
```bash
# Install Node.js LTS
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### 3. Python Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

#### 4. Frontend Dependencies
```bash
npm install
```

## Permissions Setup

The admin dashboard needs permissions to manage network configuration:

### Option 1: Sudoers Configuration (Recommended)
Create `/etc/sudoers.d/uc1-admin-network`:
```
%uc1admin ALL=(ALL) NOPASSWD: /usr/sbin/netplan
%uc1admin ALL=(ALL) NOPASSWD: /usr/sbin/ip
%uc1admin ALL=(ALL) NOPASSWD: /usr/sbin/iw
%uc1admin ALL=(ALL) NOPASSWD: /usr/bin/systemctl status bluetooth
%uc1admin ALL=(ALL) NOPASSWD: /usr/bin/bluetoothctl
```

Then add your user to the group:
```bash
sudo groupadd uc1admin
sudo usermod -a -G uc1admin $USER
# Log out and back in for changes to take effect
```

### Option 2: Run as Service
Use the systemd service created by the install script:
```bash
sudo systemctl start uc1-admin-dashboard
sudo systemctl enable uc1-admin-dashboard
```

## Verification

Check all dependencies are installed:
```bash
# Check Python
python3 --version  # Should be 3.11+

# Check Node.js
node --version     # Should be 18+
npm --version      # Should be 8+

# Check network tools
which iw           # Should show /usr/sbin/iw
which netplan      # Should show /usr/sbin/netplan
which ip           # Should show /usr/sbin/ip

# Check Docker
docker --version
docker compose version

# Check Python packages
cd backend
source venv/bin/activate
pip list
deactivate
```

## Troubleshooting

### Permission Denied Errors
- Ensure you've added your user to the `uc1admin` group
- Log out and back in after group changes
- Check sudoers file syntax: `sudo visudo -c`

### Network Tools Not Found
- Install missing tools: `sudo apt-get install iw wireless-tools`
- Ensure `/usr/sbin` is in PATH

### Python Import Errors
- Activate virtual environment: `source backend/venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend Build Errors
- Clear node_modules: `rm -rf node_modules package-lock.json`
- Reinstall: `npm install`

## Docker Image (Alternative)

For containerized deployment, all dependencies can be bundled in a Docker image:

```dockerfile
FROM ubuntu:24.04

# Install all system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    nodejs npm \
    iw wireless-tools net-tools ethtool wpasupplicant \
    htop iotop sysstat \
    && rm -rf /var/lib/apt/lists/*

# Copy and install application
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN cd backend && \
    python3 -m venv venv && \
    . venv/bin/activate && \
    pip install -r requirements.txt

# Install and build frontend
RUN npm install && npm run build

# Run backend
CMD ["backend/venv/bin/python", "backend/server.py"]
```