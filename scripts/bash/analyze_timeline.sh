#!/bin/bash

# SEC Timeline Analysis Script
# This script runs the DeepSeek AI timeline analyzer

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🤖 SEC Timeline Analyzer with DeepSeek AI${NC}"
echo -e "${PURPLE}===========================================${NC}"
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

# Check if raw data exists
if [ ! -d "$PROJECT_ROOT/data/raw" ] || [ -z "$(ls -A "$PROJECT_ROOT/data/raw" 2>/dev/null)" ]; then
    echo -e "${RED}❌ No raw SEC filing data found${NC}"
    echo -e "${YELLOW}Please download SEC filings first:${NC}"
    echo "  ./scripts/bash/download_data.sh"
    exit 1
fi

# Change to project root directory
cd "$PROJECT_ROOT"

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if required packages are installed
echo -e "${YELLOW}🔍 Checking dependencies...${NC}"
python -c "import requests, json, pathlib" 2>/dev/null || {
    echo -e "${RED}❌ Required packages not installed${NC}"
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install requests
}

# Show available tickers
echo -e "${BLUE}📊 Available tickers for analysis:${NC}"
python -c "import json; tickers = json.load(open('tickers.json')); print('  ' + ', '.join(tickers))"
echo ""

# Warn about API usage
echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo -e "${YELLOW}   • This script uses DeepSeek AI API which may incur costs${NC}"
echo -e "${YELLOW}   • Analysis includes rate limiting to respect API limits${NC}"
echo -e "${YELLOW}   • Each ticker analysis takes several minutes${NC}"
echo -e "${YELLOW}   • Results will be saved in data/analysis/${NC}"
echo ""

# Ask for confirmation
read -p "$(echo -e "${BLUE}Do you want to proceed with the analysis? (y/N): ${NC}")" -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Analysis cancelled.${NC}"
    exit 0
fi

# Run the Python script
echo -e "${GREEN}🚀 Starting timeline analysis...${NC}"
echo -e "${BLUE}This may take several minutes depending on the number of tickers...${NC}"
echo ""

python scripts/python/analyze_timeline.py

echo ""
echo -e "${GREEN}✅ Timeline analysis completed!${NC}"
echo -e "${BLUE}📁 Analysis results saved in: $PROJECT_ROOT/data/analysis${NC}"
echo ""
echo -e "${YELLOW}Generated files:${NC}"
ls -la "$PROJECT_ROOT/data/analysis/" | grep -E '\.(json)$' | while read -r line; do
    filename=$(echo "$line" | awk '{print $NF}')
    echo -e "  ${GREEN}•${NC} $filename"
done
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review analysis files in data/analysis/"
echo "  2. Use the insights for investment research"
echo "  3. Integrate with your existing workflow"
echo ""
echo -e "${PURPLE}🎉 Happy analyzing!${NC}"