#!/bin/bash

# TenMuses Development Script
# Starts both frontend and backend in development mode

set -e

echo "🚀 Starting TenMuses Development Environment"
echo "==========================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $(jobs -p) 2>/dev/null || true
    exit
}

trap cleanup EXIT INT TERM

# Start backend
echo "🔧 Starting backend..."
cd backend
source venv/bin/activate
python -m app.main &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Start frontend
echo "🎨 Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Services started!"
echo "📱 Frontend: http://localhost:3000"
echo "🔌 Backend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait
