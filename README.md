# SECChronicle

## Overview

SECChronicle is a full-stack web application that allows users to explore SEC filings for selected stock tickers. It fetches filing data from local storage, summarizes them, and displays them in a timeline format. Users can also download reports in Markdown or PDF format.

## Features

- Select from predefined tickers: TSLA, AAPL, MSFT, DVLT, RANI
- View a timeline of SEC filings with dates, types, and summaries
- Download timeline reports as Markdown or PDF
- Modern, responsive UI built with React and Tailwind CSS
- Backend powered by FastAPI

## Project Structure

- **backend/**: FastAPI server code
- **frontend/**: React application
- **data/**: Local storage for filing data (structured as /data/{ticker}/filing_folder/{filing.json, summary.json})
- **venv/**: Python virtual environment

## Setup

### Backend

1. Navigate to the project root.
2. Activate the virtual environment: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `python backend/main.py`

### Frontend

1. Navigate to `frontend/`.
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`

## Usage

- Open the frontend in your browser (usually http://localhost:5173)
- Select a ticker from the dropdown
- View the timeline of filings
- Use download buttons to get reports

## Data Preparation

### Option 1: Quick Start with Sample Data (Recommended for Testing)

1. **Create sample data**:
   ```bash
   python create_sample_data.py
   ```

   This will create sample SEC filing data for AAPL, DVLT, and RANI with realistic filing information and summaries.

### Option 2: Automated Data Download

1. **Configure tickers**: Edit `tickers.json` to specify which stock tickers you want to download data for:
   ```json
   ["AAPL", "DVLT", "RANI", "MSFT", "GOOGL"]
   ```

2. **Set up DeepSeek API** (optional, for AI summaries):
   - Get an API key from [DeepSeek](https://platform.deepseek.com/)
   - Set the environment variable: `export DEEPSEEK_API_KEY="your-api-key"`
   - Or edit the `DEEPSEEK_API_KEY` variable in `download_data.py`

3. **Run the download script**:
   ```bash
   python download_data.py
   ```

   This will:
   - Download SEC filings for the last 6 months for each ticker
   - Save filing metadata and documents in the `data/` directory
   - Generate AI summaries (if DeepSeek API key is provided)
   - Create the proper directory structure for the application

   *Note: The download script may encounter compatibility issues with some versions of edgartools. Use the sample data option for immediate testing.*

### Option 3: Manual Data Population

Create the following directory structure in the project root:

```
data/
├── AAPL/
│   ├── filing1/
│   │   ├── filing.json
│   │   └── summary.json
│   └── filing2/
│       ├── filing.json
│       └── summary.json
└── MSFT/
    └── filing1/
        ├── filing.json
        └── summary.json
```

## Bonus Features (To Implement)

- Live scraping from EDGAR
- Date filters
- Custom ticker support
- Summary regeneration

## License

MIT License
