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
3. Install dependencies if needed: `pip install -r requirements.txt` (create this if not present)
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

Populate the `data/` directory with folders for each ticker, containing subfolders with `filing.json` (metadata) and `summary.json` (DeepSeek API summary).

## Bonus Features (To Implement)

- Live scraping from EDGAR
- Date filters
- Custom ticker support
- Summary regeneration

## License

MIT License
