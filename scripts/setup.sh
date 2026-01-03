#!/bin/bash

# TenMuses Setup Script

set -e

echo "🎨 TenMuses Setup Script"
echo "========================"

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.11+ first."
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL client not found. Make sure PostgreSQL is installed."
fi

echo "✅ Prerequisites check passed"

# Setup backend
echo ""
echo "🔧 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env and configure your settings"
fi

cd ..

# Setup frontend
echo ""
echo "🎨 Setting up frontend..."
cd frontend

echo "Installing Node.js dependencies..."
npm install

if [ ! -f ".env.local" ]; then
    echo "Creating .env.local file from template..."
    cp .env.local.example .env.local
fi

cd ..

echo ""
echo "✅ Setup completed!"
echo ""
echo "📝 Next steps:"
echo "1. Configure backend/.env with your database and API keys"
echo "2. Create PostgreSQL database: createdb tenmuses"
echo "3. Start backend: cd backend && source venv/bin/activate && python -m app.main"
echo "4. Start frontend: cd frontend && npm run dev"
echo ""
echo "🌐 Access the application at http://localhost:3000"
echo "📚 API docs at http://localhost:8000/docs"
