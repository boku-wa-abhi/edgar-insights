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

### Environment Setup

1. **Configure environment variables**: Create a `.env` file in the project root:
   ```bash
   # DeepSeek API Configuration
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   
   # SEC Data Configuration
   USER_AGENT_EMAIL=your_email@example.com
   USER_AGENT_NAME=Your App Name
   ```

2. **Install python-dotenv** (if not already installed):
   ```bash
   pip install python-dotenv
   ```

### Automated Data Download (Recommended)

1. **Configure tickers**: Edit `tickers.json` to specify which stock tickers you want to download data for:
   ```json
   ["AAPL", "DVLT", "RANI", "MSFT", "GOOGL"]
   ```

2. **Set up DeepSeek API** (optional, for AI-powered timelines and summaries):
   - Get an API key from [DeepSeek](https://platform.deepseek.com/)
   - Add it to your `.env` file: `DEEPSEEK_API_KEY=your-api-key`

3. **Run the download script**:
   ```bash
   python download_data.py
   ```

   This will:
   - Download SEC filings for the last 6 months for each ticker
   - Save raw filing data in `data/raw/{ticker}/` directory
   - Generate AI-powered timelines and summaries in `data/processed/{ticker}/`
   - Create bullet-point timelines and comprehensive summaries
   - Handle API errors gracefully with fallback basic timelines

### Data Structure

The script creates an organized data structure:

```
data/
├── raw/
│   ├── AAPL/
│   │   ├── 10-Q_2024-05-02_0000320193-24-000052.json
│   │   ├── 8-K_2024-04-15_0000320193-24-000045.json
│   │   └── 10-K_2024-02-01_0000320193-24-000010.json
│   └── DVLT/
│       └── ...
└── processed/
    ├── AAPL/
    │   └── timeline_summary.json  # AI-generated timeline and summary
    └── DVLT/
        └── timeline_summary.json
```

### Manual Data Population (Advanced)

If you prefer to create your own data structure, follow the processed data format:

```json
{
  "ticker": "AAPL",
  "generated_at": "2024-01-27T10:00:00",
  "filings_analyzed": 3,
  "ai_timeline": "• 2024-05-02: Filed 10-Q...",
  "summary": "Company analysis summary...",
  "filings_metadata": [
    {
      "form": "10-Q",
      "date": "2024-05-02",
      "accession": "0000320193-24-000052"
    }
  ]
}
```

## Bonus Features (To Implement)

- Live scraping from EDGAR
- Date filters
- Custom ticker support
- Summary regeneration

## License

MIT License
