#!/bin/bash

# SEC Submissions Full Download Script
# This script activates the virtual environment and downloads all 10,089 CIKs
# with date-stamped organization and status reporting.

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_SCRIPT="$PROJECT_ROOT/scripts/python/download_sec_submissions.py"
CIK_DATABASE="$PROJECT_ROOT/data/cik_database/cik_database.json"
TODAY=$(date +%Y%m%d)

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

# Function to check if virtual environment exists and activate it
activate_venv() {
    if [[ -d "venv" ]]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
        print_success "Virtual environment activated"
    elif [[ -d ".venv" ]]; then
        print_status "Activating virtual environment..."
        source .venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_warning "No virtual environment found. Using system Python."
    fi
}

# Function to check if required files exist
check_requirements() {
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python script not found: $PYTHON_SCRIPT"
        exit 1
    fi
    
    if [[ ! -f "$CIK_DATABASE" ]]; then
        print_error "CIK database not found: $CIK_DATABASE"
        print_error "Please run the CIK download script first."
        exit 1
    fi
    
    print_success "All required files found"
}

# Function to display pre-download information
show_info() {
    print_status "=== SEC Submissions Full Download ==="
    print_status "Date: $TODAY"
    print_status "CIK Database: $CIK_DATABASE"
    print_status "Output Directory: data/submissions/$TODAY/"
    print_status "Status Report: data/submissions/$TODAY/$TODAY.md"
    print_status "Workers: 10 (concurrent downloads)"
    print_status "Delay: 1 second between requests"
    print_status "Retry Attempts: 3"
    echo
}

# Function to run the download
run_download() {
    print_status "Starting bulk download of all 10,089 CIKs..."
    print_status "This will take several hours to complete."
    print_status "You can monitor progress by checking the status report."
    echo
    
    # Run the Python script with optimal settings
    python "$PYTHON_SCRIPT" \
        --bulk "$CIK_DATABASE" \
        --workers 10 \
        --delay 1 \
        --retry-attempts 3
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "Download completed successfully!"
        show_summary
    else
        print_error "Download failed with exit code: $exit_code"
        print_error "Check the logs for more details."
        exit $exit_code
    fi
}

# Function to show download summary
show_summary() {
    echo
    print_status "=== Download Summary ==="
    
    # Count downloaded folders
    if [[ -d "data/submissions/$TODAY" ]]; then
        local folder_count=$(find "data/submissions/$TODAY/CIK" -maxdepth 1 -type d 2>/dev/null | grep -v "^data/submissions/$TODAY/CIK$" | wc -l | tr -d ' ')
        print_status "Total folders created: $folder_count"
    fi
    
    # Show status report location
    if [[ -f "data/submissions/$TODAY/$TODAY.md" ]]; then
        print_status "Status report: data/submissions/$TODAY/$TODAY.md"
        print_status "Individual company data: data/submissions/$TODAY/CIK/*/"
    fi
    
    print_success "All data has been organized by date: $TODAY"
}

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Download all 10,089 CIKs from SEC EDGAR with date-stamped organization"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -y, --yes      Skip confirmation prompt"
    echo ""
    echo "This script will:"
    echo "  1. Activate virtual environment (if available)"
    echo "  2. Download all CIKs to data/submissions/$TODAY/CIK/*/"
    echo "  3. Generate status report at data/submissions/$TODAY/$TODAY.md"
    echo "  4. Use 10 concurrent workers with 1-second delays"
    echo "  5. Retry failed downloads up to 3 times"
}

# Function to confirm download
confirm_download() {
    if [[ "$1" == "-y" ]] || [[ "$1" == "--yes" ]]; then
        return 0
    fi
    
    echo
    print_warning "This will download data for all 10,089 companies."
    print_warning "The process may take several hours to complete."
    echo
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        print_status "Download cancelled."
        exit 0
    fi
}

# Main execution
main() {
    # Parse command line arguments
    case "${1:-}" in
        -h|--help)
            show_usage
            exit 0
            ;;
        -y|--yes)
            local skip_confirm=true
            ;;
        "")
            local skip_confirm=false
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
    
    # Run the download process
    show_info
    check_requirements
    
    if [[ "$skip_confirm" != true ]]; then
        confirm_download
    fi
    
    activate_venv
    run_download
}

# Run main function with all arguments
main "$@"