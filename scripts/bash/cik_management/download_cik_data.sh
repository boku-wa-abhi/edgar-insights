#!/bin/bash

# EDGAR CIK Data Download Script
# This script downloads all company CIK numbers from SEC EDGAR database
# and saves them locally in CSV and JSON formats.

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PYTHON_SCRIPT="$PROJECT_ROOT/scripts/python/cik_management/download_cik_data.py"
DATA_DIR="$PROJECT_ROOT/data/cik_database"
LOG_FILE="$DATA_DIR/cik_download.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    print_status "Using Python: $PYTHON_CMD"
}

# Function to check and install required Python packages
check_dependencies() {
    print_status "Checking Python dependencies..."
    
    # Check if requests is installed
    if ! $PYTHON_CMD -c "import requests" &> /dev/null; then
        print_warning "requests package not found. Installing..."
        $PYTHON_CMD -m pip install requests
    fi
    
    print_success "All dependencies are available"
}

# Function to create necessary directories
setup_directories() {
    print_status "Setting up directories..."
    mkdir -p "$DATA_DIR"
    print_success "Directories created: $DATA_DIR"
}

# Function to run the Python script
run_download() {
    print_status "Starting CIK data download..."
    print_status "This may take a few minutes depending on your internet connection..."
    
    cd "$(dirname "$PYTHON_SCRIPT")"
    
    if $PYTHON_CMD "$(basename "$PYTHON_SCRIPT")"; then
        print_success "CIK data download completed successfully!"
        return 0
    else
        print_error "CIK data download failed!"
        return 1
    fi
}

# Function to display download summary
show_summary() {
    if [[ -f "$DATA_DIR/download_summary.json" ]]; then
        print_status "Download Summary:"
        if command -v jq &> /dev/null; then
            # Use jq for pretty printing if available
            jq -r '
                "Total Companies: " + (.total_companies | tostring) + "\n" +
                "Companies with Tickers: " + (.companies_with_tickers | tostring) + "\n" +
                "Companies without Tickers: " + (.companies_without_tickers | tostring) + "\n" +
                "Download Time: " + .download_timestamp
            ' "$DATA_DIR/download_summary.json"
        else
            # Fallback to basic display
            cat "$DATA_DIR/download_summary.json"
        fi
    fi
    
    print_status "Files created:"
    ls -la "$DATA_DIR"/*.{json,csv} 2>/dev/null || print_warning "No output files found"
}

# Function to display usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Download all company CIK numbers from SEC EDGAR database"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo "  -q, --quiet    Suppress non-error output"
    echo ""
    echo "Output files will be saved to: $DATA_DIR"
    echo "  - company_tickers.json (raw SEC data)"
    echo "  - cik_database.csv (processed CSV format)"
    echo "  - cik_database.json (processed JSON format)"
    echo "  - download_summary.json (summary report)"
}

# Function to handle cleanup on exit
cleanup() {
    if [[ $? -ne 0 ]]; then
        print_error "Script failed. Check the log file: $LOG_FILE"
    fi
}

# Set up trap for cleanup
trap cleanup EXIT

# Main execution
main() {
    local verbose=false
    local quiet=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -q|--quiet)
                quiet=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Suppress output if quiet mode
    if [[ "$quiet" == "true" ]]; then
        exec > /dev/null 2>&1
    fi
    
    print_status "EDGAR CIK Data Downloader"
    print_status "========================="
    
    # Run the download process
    check_python
    check_dependencies
    setup_directories
    
    if run_download; then
        show_summary
        print_success "CIK data download process completed!"
        print_status "Data saved to: $DATA_DIR"
    else
        exit 1
    fi
}

# Run main function with all arguments
main "$@"