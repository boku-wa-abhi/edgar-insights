#!/bin/bash

# SEC Submissions Bulk Download Script
# This script activates the virtual environment and downloads all CIKs from the database

set -e  # Exit on any error

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== SEC Submissions Bulk Download ==="
echo "Project root: $PROJECT_ROOT"
echo "Starting at: $(date)"

# Change to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found at .venv"
    echo "Please create a virtual environment first:"
    echo "  python -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if required packages are installed
echo "Checking dependencies..."
python -c "import requests, concurrent.futures" 2>/dev/null || {
    echo "Error: Required packages not installed"
    echo "Please install dependencies:"
    echo "  pip install requests"
    exit 1
}

# Check if CIK database exists
CIK_DATABASE="data/cik_database/cik_database.json"
if [ ! -f "$CIK_DATABASE" ]; then
    echo "Error: CIK database not found at $CIK_DATABASE"
    exit 1
fi

# Get total companies from database
TOTAL_COMPANIES=$(python -c "import json; data=json.load(open('$CIK_DATABASE')); print(data['metadata']['total_companies'])")
echo "Total companies in database: $TOTAL_COMPANIES"

# Create output directory if it doesn't exist
mkdir -p data/submissions

# Run the download script with optimal settings
echo "Starting bulk download..."
echo "Settings:"
echo "  - Workers: 10 (concurrent downloads)"
echo "  - Delay: 2 seconds (between downloads)"
echo "  - Retry attempts: 3"
echo "  - Output directory: data/submissions"
echo ""

python scripts/python/download_sec_submissions.py \
    --bulk "$CIK_DATABASE" \
    --workers 10 \
    --delay 2 \
    --retry-attempts 3 \
    --output-dir data/submissions

DOWNLOAD_EXIT_CODE=$?

echo ""
echo "=== Download Summary ==="
echo "Completed at: $(date)"

# Count downloaded folders (in today's date directory)
TODAY=$(date +%Y%m%d)
if [ -d "data/submissions/$TODAY/CIK" ]; then
    DOWNLOADED_COUNT=$(find data/submissions/$TODAY/CIK -maxdepth 1 -type d | grep -v "^data/submissions/$TODAY/CIK$" | wc -l | tr -d ' ')
else
    DOWNLOADED_COUNT=0
fi
echo "Downloaded folders: $DOWNLOADED_COUNT"
echo "Expected total: $TOTAL_COMPANIES"
echo "Download date: $TODAY"

if [ $DOWNLOAD_EXIT_CODE -eq 0 ]; then
    echo "✅ Download script completed successfully"
else
    echo "❌ Download script exited with error code: $DOWNLOAD_EXIT_CODE"
fi

# Check if all downloads completed
if [ "$DOWNLOADED_COUNT" -eq "$TOTAL_COMPANIES" ]; then
    echo "🎉 All $TOTAL_COMPANIES companies downloaded successfully!"
else
    REMAINING=$((TOTAL_COMPANIES - DOWNLOADED_COUNT))
    echo "⚠️  Still need to download $REMAINING companies"
    echo "You can re-run this script to retry failed downloads"
fi

echo ""
echo "Results saved to: data/submissions/$TODAY/download_results.json"
echo "Status report: data/submissions/$TODAY/$TODAY.md"
echo "Individual company data in: data/submissions/$TODAY/CIK/*/"

exit $DOWNLOAD_EXIT_CODE