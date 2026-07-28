#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting UC-1 Pro Admin Dashboard Development Server${NC}"

# Kill any existing processes
echo -e "${YELLOW}Stopping any existing processes...${NC}"
pkill -f "python.*server.py" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 2

# Navigate to the admin dashboard directory
cd /home/ucadmin/UC-1-Pro/services/admin-dashboard

# Activate virtual environment and start backend
echo -e "${GREEN}Starting backend server on port 8085...${NC}"
(
    source venv/bin/activate
    export PYTHONUNBUFFERED=1
    python backend/server.py 2>&1 | sed 's/^/[BACKEND] /'
) &
BACKEND_PID=$!

# Give backend time to start
sleep 3

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Backend failed to start! Check the logs above.${NC}"
    exit 1
fi

# Start frontend
echo -e "${GREEN}Starting frontend dev server on port 8084...${NC}"
(
    npm run dev -- --host 0.0.0.0 2>&1 | sed 's/^/[FRONTEND] /'
) &
FRONTEND_PID=$!

# Give frontend time to start
sleep 3

# Display status
echo -e "\n${GREEN}Services are running:${NC}"
echo -e "  ${YELLOW}Frontend:${NC} http://0.0.0.0:8084"
echo -e "  ${YELLOW}Backend API:${NC} http://0.0.0.0:8085"
echo -e "\n${YELLOW}Process IDs:${NC}"
echo -e "  Backend: $BACKEND_PID"
echo -e "  Frontend: $FRONTEND_PID"
echo -e "\n${YELLOW}Press Ctrl+C to stop both servers${NC}\n"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    pkill -f "python.*server.py" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    echo -e "${GREEN}Servers stopped.${NC}"
    exit 0
}

# Set trap for Ctrl+C
trap cleanup INT

# Keep script running and show logs
while true; do
    # Check if processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}Backend crashed! Check the logs.${NC}"
        cleanup
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}Frontend crashed! Check the logs.${NC}"
        cleanup
    fi
    sleep 5
done