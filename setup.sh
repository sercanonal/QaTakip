#!/bin/bash

# QA Hub - Quick Setup Script
# This script sets up both backend and frontend

set -e

echo "🚀 QA Hub Setup"
echo "==============="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 18+${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python and Node.js found${NC}"

# Backend Setup
echo ""
echo "📦 Setting up Backend..."
cd backend

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install requirements
echo "  Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

# Create data directory
mkdir -p data

echo -e "${GREEN}✓ Backend ready${NC}"

cd ..

# Frontend Setup
echo ""
echo "📦 Setting up Frontend..."
cd frontend

# Install npm packages
echo "  Installing npm packages..."
npm install --silent

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env
    echo "  Created .env file"
fi

echo -e "${GREEN}✓ Frontend ready${NC}"

cd ..

echo ""
echo "========================================"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To start the application:"
echo ""
echo "  1. Start Backend (Terminal 1):"
echo "     cd backend"
echo "     source venv/bin/activate"
echo "     uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
echo ""
echo "  2. Start Frontend (Terminal 2):"
echo "     cd frontend"
echo "     npm start"
echo ""
echo "  3. Open http://localhost:3000"
echo ""
echo "Or use: ./run.sh to start both"
echo "========================================"
