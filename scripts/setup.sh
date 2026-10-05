#!/bin/bash
# ============================================================
# BharatRoad Twin - Linux/Mac Setup Script
# Run this once to set up the development environment.
# ============================================================

set -e

echo ""
echo "========================================"
echo " BharatRoad Twin - Setup"
echo "========================================"
echo ""

# Find Python 3
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] Python 3 not found. Please install Python 3.11+"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  Mac: brew install python@3.11"
    exit 1
fi

echo "[INFO] Using Python: $PYTHON_CMD"
$PYTHON_CMD --version

# Create virtual environment
echo ""
echo "[1/4] Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
fi
source venv/bin/activate

# Install backend dependencies
echo ""
echo "[2/4] Installing backend Python dependencies..."
pip install -r backend/requirements.txt

# Copy .env if not exists
echo ""
echo "[3/4] Setting up environment file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[INFO] Created .env from .env.example - please review and adjust settings."
else
    echo "[INFO] .env already exists, skipping."
fi

# Check for Node.js
echo ""
echo "[4/4] Checking Node.js..."
if command -v node &> /dev/null; then
    echo "[INFO] Node.js found: $(node --version)"
    echo "[INFO] Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "[WARNING] Node.js not found. Install from https://nodejs.org for the frontend."
fi

echo ""
echo "========================================"
echo " Setup Complete!"
echo "========================================"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run the backend:"
echo "  source venv/bin/activate"
echo "  cd backend"
echo "  uvicorn app.main:app --reload"
echo ""
echo "To run the frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Optional: Install SUMO"
echo "  Ubuntu: sudo apt install sumo sumo-tools"
echo "  Mac: brew install sumo"
echo "  Set SUMO_HOME environment variable after install."
echo ""
