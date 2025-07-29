#!/bin/bash

# CIK Data Update Scheduler
# This script helps set up automated CIK data updates using cron
# The SEC updates their company tickers file regularly, so we should update our local copy periodically

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DOWNLOAD_SCRIPT="$SCRIPT_DIR/download_cik_data.sh"
LOG_DIR="$PROJECT_ROOT/data/cik_database/logs"
CRON_LOG="$LOG_DIR/cron_updates.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Function to create log directory
setup_logging() {
    mkdir -p "$LOG_DIR"
    touch "$CRON_LOG"
}

# Function to show recommended update frequencies
show_recommendations() {
    cat << EOF
${BLUE}CIK Data Update Frequency Recommendations:${NC}

${GREEN}Recommended Schedule: Weekly (Every Sunday at 2 AM)${NC}
- The SEC updates company information regularly but not daily
- Weekly updates ensure you have current data without overwhelming SEC servers
- Sunday early morning minimizes impact on business operations

${YELLOW}Alternative Schedules:${NC}

1. ${BLUE}Conservative (Monthly):${NC}
   - First Sunday of each month at 2 AM
   - Good for: Low-frequency analysis, reduced server load
   - Cron: 0 2 1-7 * 0

2. ${BLUE}Standard (Weekly):${NC}
   - Every Sunday at 2 AM
   - Good for: Regular analysis, balanced approach
   - Cron: 0 2 * * 0

3. ${BLUE}Frequent (Bi-weekly):${NC}
   - Every other Sunday at 2 AM
   - Good for: Active trading analysis
   - Cron: 0 2 * * 0 (with additional logic)

4. ${BLUE}High-frequency (Daily):${NC}
   - Every day at 2 AM
   - ${RED}NOT RECOMMENDED${NC} - May violate SEC rate limits
   - Only use if you have special requirements

${YELLOW}Important Notes:${NC}
- Always respect SEC rate limits (10 requests per second max)
- The SEC may block excessive requests
- Consider your actual data freshness needs
- Monitor logs for any issues

EOF
}

# Function to install cron job
install_cron() {
    local frequency="$1"
    local cron_schedule
    
    case "$frequency" in
        "weekly")
            cron_schedule="0 2 * * 0"
            print_status "Setting up weekly CIK updates (Sundays at 2 AM)"
            ;;
        "monthly")
            cron_schedule="0 2 1-7 * 0"
            print_status "Setting up monthly CIK updates (First Sunday at 2 AM)"
            ;;
        "daily")
            cron_schedule="0 2 * * *"
            print_warning "Setting up daily CIK updates (NOT RECOMMENDED)"
            print_warning "This may violate SEC rate limits!"
            ;;
        *)
            print_error "Invalid frequency. Use: weekly, monthly, or daily"
            return 1
            ;;
    esac
    
    # Create the cron command
    local cron_command="$cron_schedule cd '$PROJECT_ROOT' && '$DOWNLOAD_SCRIPT' --quiet >> '$CRON_LOG' 2>&1"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "download_cik_data.sh"; then
        print_warning "CIK update cron job already exists. Removing old job..."
        crontab -l 2>/dev/null | grep -v "download_cik_data.sh" | crontab -
    fi
    
    # Add new cron job
    (crontab -l 2>/dev/null; echo "$cron_command") | crontab -
    
    print_success "Cron job installed successfully!"
    print_status "Schedule: $cron_schedule"
    print_status "Command: $cron_command"
    print_status "Logs will be written to: $CRON_LOG"
}

# Function to remove cron job
remove_cron() {
    if crontab -l 2>/dev/null | grep -q "download_cik_data.sh"; then
        crontab -l 2>/dev/null | grep -v "download_cik_data.sh" | crontab -
        print_success "CIK update cron job removed successfully!"
    else
        print_warning "No CIK update cron job found"
    fi
}

# Function to show current cron jobs
show_cron() {
    print_status "Current cron jobs related to CIK updates:"
    if crontab -l 2>/dev/null | grep -q "download_cik_data.sh"; then
        crontab -l 2>/dev/null | grep "download_cik_data.sh"
    else
        print_warning "No CIK update cron jobs found"
    fi
}

# Function to test the download script
test_download() {
    print_status "Testing CIK download script..."
    if "$DOWNLOAD_SCRIPT" --verbose; then
        print_success "Download script test completed successfully!"
    else
        print_error "Download script test failed!"
        return 1
    fi
}

# Function to show logs
show_logs() {
    if [[ -f "$CRON_LOG" ]]; then
        print_status "Recent cron update logs:"
        tail -20 "$CRON_LOG"
    else
        print_warning "No cron logs found at: $CRON_LOG"
    fi
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
  install [frequency]  Install cron job for automatic updates
                      frequency: weekly (default), monthly, daily
  remove              Remove existing cron job
  status              Show current cron job status
  test                Test the download script
  logs                Show recent update logs
  recommendations     Show update frequency recommendations
  help                Show this help message

Examples:
  $0 install weekly          # Install weekly updates (recommended)
  $0 install monthly         # Install monthly updates
  $0 remove                  # Remove automatic updates
  $0 status                  # Check current schedule
  $0 test                    # Test download functionality

EOF
}

# Main function
main() {
    setup_logging
    
    case "${1:-help}" in
        "install")
            local frequency="${2:-weekly}"
            install_cron "$frequency"
            ;;
        "remove")
            remove_cron
            ;;
        "status")
            show_cron
            ;;
        "test")
            test_download
            ;;
        "logs")
            show_logs
            ;;
        "recommendations")
            show_recommendations
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"