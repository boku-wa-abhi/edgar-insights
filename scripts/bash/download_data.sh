#!/bin/bash

# SEC Data Download Script
# This script runs the Python SEC filing downloader

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 SEC Filing Downloader${NC}"
echo -e "${BLUE}=========================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${RED}❌ Virtual environment not found at $PROJECT_ROOT/venv${NC}"
    echo -e "${YELLOW}Please create a virtual environment first:${NC}"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if tickers.json exists
if [ ! -f "$PROJECT_ROOT/tickers.json" ]; then
    echo -e "${RED}❌ tickers.json not found at $PROJECT_ROOT/tickers.json${NC}"
    echo -e "${YELLOW}Please create tickers.json with your stock symbols${NC}"
    exit 1
fi

# Change to project root directory
cd "$PROJECT_ROOT"

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if required packages are installed
echo -e "${YELLOW}🔍 Checking dependencies...${NC}"
python -c "import sec_edgar_downloader, dotenv" 2>/dev/null || {
    echo -e "${RED}❌ Required packages not installed${NC}"
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install sec-edgar-downloader python-dotenv
}

# Parse command line arguments
FORCE_DOWNLOAD=false
if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
    FORCE_DOWNLOAD=true
    echo -e "${YELLOW}⚠️  Force download mode enabled - will re-download existing data${NC}"
fi

# Run the Python script
echo -e "${GREEN}🏃 Running SEC filing downloader...${NC}"
echo ""

if [ "$FORCE_DOWNLOAD" = true ]; then
    python scripts/python/download_data.py --force
else
    python scripts/python/download_data.py
fi

echo ""
echo -e "${GREEN}✅ Download script completed!${NC}"
echo -e "${BLUE}📁 Data saved in: $PROJECT_ROOT/data/raw${NC}"
echo ""
echo -e "${YELLOW}Usage:${NC}"
echo "  ./scripts/bash/download_data.sh          # Normal download (skip existing)"
echo "  ./scripts/bash/download_data.sh --force  # Force re-download all data"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Start backend: cd backend && python main.py"
echo "  2. Start frontend: cd frontend && npm run dev"
echo "  3. Open http://localhost:5173"