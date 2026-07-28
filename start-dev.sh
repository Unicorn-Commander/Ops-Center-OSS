#!/bin/bash

# Set development mode
export DEVELOPMENT=true

# Kill existing processes
echo "Stopping any existing processes..."
killall -q python3 2>/dev/null
killall -q node 2>/dev/null
sleep 2

# Start backend
echo "Starting backend on port 8085..."
cd /home/ucadmin/UC-1-Pro/services/admin-dashboard
source venv/bin/activate
python backend/server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend on port 8084..."
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

echo "Services started:"
echo "  Frontend: http://localhost:8084"
echo "  Backend: http://localhost:8085"
echo ""
echo "PIDs: Backend=$BACKEND_PID, Frontend=$FRONTEND_PID"
echo "Press Enter to stop both servers..."

read

# Cleanup
echo "Stopping servers..."
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
killall -q python3 2>/dev/null
killall -q node 2>/dev/null