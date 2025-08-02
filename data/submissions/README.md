# SEC Submissions Data

This directory contains SEC submissions data downloaded from the SEC's official API endpoint: `https://data.sec.gov/submissions/CIK##########.json`

## Data Structure

The SEC submissions API provides comprehensive filing history and metadata for entities registered with the SEC <mcreference link="https://www.sec.gov/search-filings/edgar-application-programming-interfaces" index="1">1</mcreference>. Each entity's data is organized by their 10-digit Central Index Key (CIK).

### Directory Organization

```
data/submissions/
├── CIK{10-digit-cik}/
│   ├── submissions.json    # Complete submissions data from SEC API
│   └── summary.json        # Extracted key information and metadata
└── README.md              # This documentation
```

### Data Content

#### submissions.json
Contains the complete response from the SEC submissions API, including:

- **Entity Information**: Company name, CIK, entity type, SIC code, incorporation details
- **Contact Information**: Business and mailing addresses, phone numbers
- **Corporate Details**: Ticker symbols, exchanges, EIN, fiscal year end
- **Filing History**: Comprehensive list of all SEC filings with:
  - Accession numbers
  - Form types (10-K, 10-Q, 8-K, 13F-HR, etc.)
  - Filing dates
  - Report dates
  - Document counts
  - File numbers
  - Film numbers

#### summary.json
Extracted key information for quick reference:

- Basic entity details (name, CIK, SIC)
- Corporate structure (state of incorporation, entity type)
- Trading information (tickers, exchanges)
- Contact details (phone, addresses)
- Filing statistics (total count)
- Download timestamp

## Data Types Available

The submissions data includes all types of SEC filings <mcreference link="https://www.sec.gov/search-filings/edgar-application-programming-interfaces" index="4">4</mcreference>:

- **Periodic Reports**: 10-K, 10-Q, 8-K
- **Ownership Reports**: 13F-HR, 13G, 13D, Forms 3/4/5
- **Registration Statements**: S-1, S-3, etc.
- **Proxy Statements**: DEF 14A
- **Investment Company Reports**: N-PORT, N-CEN
- **And many more form types**

## Usage Examples

### Download Submissions Data

```bash
# Download for a specific CIK
python scripts/python/download_sec_submissions.py --cik 0002012383

# Specify custom output directory
python scripts/python/download_sec_submissions.py --cik 0002012383 --output-dir data/custom_submissions
```

### Example: BlackRock, Inc. (CIK: 0002012383)

The test download for BlackRock shows:
- **Company**: BlackRock, Inc.
- **Entity Type**: Operating company
- **SIC**: 6211 - Security Brokers, Dealers & Flotation Companies
- **Ticker**: BLK (NYSE)
- **Recent Filings**: 3,933 filings available
- **Form Types**: Includes SCHEDULE 13G, Form 4, Form 144, and amendments

## Data Freshness

The SEC API data is updated in real-time throughout the day as new submissions are disseminated <mcreference link="https://www.sec.gov/search-filings/edgar-application-programming-interfaces" index="4">4</mcreference>. The JSON structures reflect the current state of filings and are continuously updated.

## API Rate Limits

The SEC requires a User-Agent header for all requests to identify the requester for rate-limiting purposes <mcreference link="https://sec-edgar-api.readthedocs.io/" index="5">5</mcreference>. Our script includes an appropriate User-Agent header to comply with SEC requirements.

## Related Data

This submissions data complements other data in the project:
- **CIK Database** (`data/cik_database/`): Maps tickers to CIKs
- **SEC Filings** (`data/sec_filings/`): Raw filing documents (13F-HR text files)
- **Analysis** (`data/analysis/`): Processed and analyzed data

## Data Schema

For detailed information about the JSON schema and available fields, refer to the SEC's official API documentation at: https://www.sec.gov/search-filings/edgar-application-programming-interfaces