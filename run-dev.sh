#!/bin/bash

# Kill any existing processes on ports 8084 and 8085
echo "Checking for existing processes..."
lsof -ti:8084 | xargs -r kill -9 2>/dev/null
lsof -ti:8085 | xargs -r kill -9 2>/dev/null

# Start the backend server
echo "Starting backend server..."
source venv/bin/activate
python backend/server.py &
BACKEND_PID=$!

# Give backend a moment to start
sleep 2

# Start the frontend dev server
echo "Starting frontend dev server..."
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Services are running:"
echo "  - Backend API: http://0.0.0.0:8085"
echo "  - Frontend Dev: http://0.0.0.0:8084"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait