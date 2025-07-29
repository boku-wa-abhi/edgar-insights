# CIK Management Scripts

This directory contains scripts for downloading, managing, and querying SEC EDGAR CIK (Central Index Key) data.

## Overview

The SEC maintains a database of all public companies with their corresponding CIK numbers, which are unique identifiers used in EDGAR filings. These scripts help you:

1. Download all company CIK data from SEC EDGAR
2. Process and store it in searchable formats (CSV and JSON)
3. Set up automated updates
4. Query and search the local database

## Files

- `download_cik_data.py` - Main Python script to download CIK data
- `cik_lookup.py` - Utility script to search and query CIK data
- `README.md` - This documentation file

## Quick Start

### 1. Download CIK Data

```bash
# Using Python script directly
cd scripts/python/cik_management
python3 download_cik_data.py

# Using bash wrapper (recommended)
cd scripts/bash/cik_management
./download_cik_data.sh
```

### 2. Search Companies

```bash
# Search by ticker
python3 cik_lookup.py --ticker AAPL

# Search by CIK number
python3 cik_lookup.py --cik 0000320193

# Search by company name
python3 cik_lookup.py --search "Apple"

# Get database statistics
python3 cik_lookup.py --stats
```

### 3. Set Up Automated Updates

```bash
# Set up weekly updates (recommended)
cd scripts/bash/cik_management
./schedule_cik_updates.sh install weekly

# Check current schedule
./schedule_cik_updates.sh status

# Remove automated updates
./schedule_cik_updates.sh remove
```

## Detailed Usage

### Download Script (`download_cik_data.py`)

Downloads the complete list of companies from SEC EDGAR and saves them in multiple formats:

**Output Files:**
- `data/cik_database/company_tickers.json` - Raw SEC data
- `data/cik_database/cik_database.csv` - Processed CSV format
- `data/cik_database/cik_database.json` - Processed JSON format
- `data/cik_database/download_summary.json` - Summary report

**Features:**
- Respects SEC rate limits
- Comprehensive error handling
- Detailed logging
- Data validation and processing

### Lookup Script (`cik_lookup.py`)

Provides various ways to search and query the downloaded CIK data:

```bash
# Lookup by ticker symbol
python3 cik_lookup.py --ticker MSFT

# Lookup by CIK number (padded or unpadded)
python3 cik_lookup.py --cik 789019
python3 cik_lookup.py --cik 0000789019

# Exact company name search
python3 cik_lookup.py --name "Microsoft Corporation"

# Fuzzy search (searches both ticker and name)
python3 cik_lookup.py --search microsoft

# Limit search results
python3 cik_lookup.py --search tech --limit 5

# Output in JSON format
python3 cik_lookup.py --ticker AAPL --json

# Database statistics
python3 cik_lookup.py --stats
```

### Bash Scripts

The bash scripts provide convenient wrappers and automation:

#### `download_cik_data.sh`

```bash
# Basic download
./download_cik_data.sh

# Verbose output
./download_cik_data.sh --verbose

# Quiet mode (for cron jobs)
./download_cik_data.sh --quiet

# Help
./download_cik_data.sh --help
```

#### `schedule_cik_updates.sh`

```bash
# Install weekly updates (recommended)
./schedule_cik_updates.sh install weekly

# Install monthly updates
./schedule_cik_updates.sh install monthly

# Check current cron jobs
./schedule_cik_updates.sh status

# Test the download script
./schedule_cik_updates.sh test

# View recent logs
./schedule_cik_updates.sh logs

# Remove automated updates
./schedule_cik_updates.sh remove

# Show frequency recommendations
./schedule_cik_updates.sh recommendations
```

## Update Frequency Recommendations

### Recommended: Weekly Updates
- **Schedule:** Every Sunday at 2 AM
- **Rationale:** SEC updates company information regularly but not daily
- **Cron:** `0 2 * * 0`

### Alternative Schedules:

1. **Monthly (Conservative):**
   - First Sunday of each month at 2 AM
   - Good for low-frequency analysis
   - Cron: `0 2 1-7 * 0`

2. **Bi-weekly (Active):**
   - Every other Sunday at 2 AM
   - Good for active trading analysis

3. **Daily (Not Recommended):**
   - May violate SEC rate limits
   - Only use if absolutely necessary

## Data Format

### CSV Format (`cik_database.csv`)
```csv
ticker,company_name,cik,cik_raw,last_updated
AAPL,Apple Inc.,0000320193,320193,2024-01-15T10:30:00
MSFT,Microsoft Corporation,0000789019,789019,2024-01-15T10:30:00
```

### JSON Format (`cik_database.json`)
```json
{
  "metadata": {
    "total_companies": 12000,
    "last_updated": "2024-01-15T10:30:00",
    "source": "SEC EDGAR company_tickers.json"
  },
  "companies": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "cik": "0000320193",
      "cik_raw": "320193",
      "last_updated": "2024-01-15T10:30:00"
    }
  ]
}
```

## Requirements

- Python 3.6+
- `requests` library
- Internet connection
- Sufficient disk space (~5-10 MB for data files)

## Installation

```bash
# Install Python dependencies
pip3 install requests

# Make scripts executable
chmod +x ../bash/cik_management/*.sh
```

## Troubleshooting

### Common Issues

1. **"requests module not found"**
   ```bash
   pip3 install requests
   ```

2. **"Permission denied" when running bash scripts**
   ```bash
   chmod +x scripts/bash/cik_management/*.sh
   ```

3. **SEC rate limit errors**
   - Wait a few minutes and try again
   - The script includes built-in delays to respect rate limits

4. **Cron job not working**
   - Check cron logs: `./schedule_cik_updates.sh logs`
   - Test the script manually: `./schedule_cik_updates.sh test`
   - Ensure full paths are used in cron jobs

### Logs

- Download logs: `data/cik_database/cik_download.log`
- Cron logs: `data/cik_database/logs/cron_updates.log`

## SEC Compliance

- Scripts respect SEC rate limits (10 requests per second maximum)
- Includes proper User-Agent headers as required by SEC
- Uses official SEC endpoints
- Implements appropriate delays between requests

## Data Sources

- **Primary:** https://www.sec.gov/files/company_tickers.json
- **Documentation:** https://www.sec.gov/edgar/sec-api-documentation

## License

This project is for educational and research purposes. Please comply with SEC terms of service when using EDGAR data.