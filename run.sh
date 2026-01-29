#!/bin/bash

# QA Hub - Run Script
# Starts both backend and frontend

echo "🚀 Starting QA Hub..."

# Kill any existing processes on ports 8001 and 3000
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start Backend
echo "📦 Starting Backend on port 8001..."
cd backend
source venv/bin/activate 2>/dev/null || {
    echo "Virtual environment not found. Running setup first..."
    cd ..
    ./setup.sh
    cd backend
    source venv/bin/activate
}

uvicorn server:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start Frontend
echo "📦 Starting Frontend on port 3000..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "✅ QA Hub is running!"
echo ""
echo "   Backend:  http://localhost:8001"
echo "   Frontend: http://localhost:3000"
echo ""
echo "   Press Ctrl+C to stop"
echo "========================================"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
