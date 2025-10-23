#!/bin/bash

# Production Trading System Startup Script
# Usage: ./start_trading.sh

set -e  # Exit on error

echo "========================================"
echo "  PRODUCTION TRADING SYSTEM"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found${NC}"
    echo "Please create .env from .env.example:"
    echo "  cp .env.example .env"
    echo "  nano .env  # Add your credentials"
    exit 1
fi

# Load environment variables
echo "Loading environment variables..."
set -a
source .env
set +a

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 not found${NC}"
    exit 1
fi

# Check required packages
echo "Checking dependencies..."
python3 -c "import requests, pandas, numpy" 2>/dev/null || {
    echo -e "${YELLOW}Installing missing dependencies...${NC}"
    pip install -q requests pandas numpy
}

# Run configuration check
echo "Validating configuration..."
python3 config/trading_config.py || {
    echo -e "${RED}Configuration validation failed${NC}"
    exit 1
}

# Create necessary directories
mkdir -p logs data/backups

echo ""
echo -e "${GREEN}✓ All checks passed${NC}"
echo ""

# Show mode
MODE=$(python3 -c "from config.trading_config import config; print('DEMO' if config.is_demo() else 'LIVE')")

if [ "$MODE" = "LIVE" ]; then
    echo -e "${RED}========================================"
    echo "  ⚠️  LIVE TRADING MODE ⚠️"
    echo "========================================${NC}"
    echo ""
    echo "You are about to start LIVE trading with REAL money."
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Start trading system
echo ""
echo "Starting trading system..."
echo ""

python3 trading_system.py
