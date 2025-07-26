#!/usr/bin/env python3
"""
SEC Filing Data Download Script for SECChronicle
Downloads SEC filings and generates AI-powered summaries and timelines
"""

import json
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DATA_DIR = "data"
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
TICKERS_FILE = "tickers.json"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
USER_AGENT_EMAIL = os.getenv("USER_AGENT_EMAIL", "contact@example.com")
USER_AGENT_NAME = os.getenv("USER_AGENT_NAME", "SECChronicle Data Scraper")

class SECDataDownloader:
    """Handles SEC data downloading and processing"""
    
    def __init__(self):
        self.setup_directories()
        self.setup_edgar_identity()
    
    def setup_directories(self):
        """Create necessary directories"""
        Path(DATA_DIR).mkdir(exist_ok=True)
        Path(RAW_DATA_DIR).mkdir(exist_ok=True)
        Path(PROCESSED_DATA_DIR).mkdir(exist_ok=True)
    
    def setup_edgar_identity(self):
        """Set up EDGAR identity for API access"""
        try:
            from edgar import set_identity
            set_identity(f"{USER_AGENT_NAME} {USER_AGENT_EMAIL}")
            print(f"✓ EDGAR identity set: {USER_AGENT_NAME} {USER_AGENT_EMAIL}")
        except ImportError:
            print("⚠ Warning: edgartools not available. Install with: pip install edgartools")
            return False
        return True
    
    def load_tickers(self) -> List[str]:
        """Load tickers from JSON file"""
        try:
            with open(TICKERS_FILE, 'r') as f:
                tickers = json.load(f)
            print(f"✓ Loaded {len(tickers)} tickers: {', '.join(tickers)}")
            return tickers
        except FileNotFoundError:
            print(f"⚠ {TICKERS_FILE} not found. Creating default file...")
            default_tickers = ["AAPL", "DVLT", "RANI"]
            with open(TICKERS_FILE, 'w') as f:
                json.dump(default_tickers, f, indent=2)
            return default_tickers
    
    def download_filings_for_ticker(self, ticker: str) -> bool:
        """Download filings for a specific ticker"""
        try:
            from edgar import Company
            
            print(f"\nProcessing ticker: {ticker}")
            
            # Get company
            company = Company(ticker)
            print(f"Company: {company.name}")
            
            # Calculate date range (last 6 months)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            
            print(f"Fetching filings from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Get filings with error handling
            try:
                filings = company.get_filings(form=['10-K', '10-Q', '8-K', 'DEF 14A'], 
                                             date=f"{start_date.strftime('%Y-%m-%d')}:{end_date.strftime('%Y-%m-%d')}")
            except Exception as e:
                print(f"  ⚠ Error with date range, trying without date filter: {e}")
                filings = company.get_filings(form=['10-K', '10-Q', '8-K', 'DEF 14A'])
                # Filter manually
                filtered_filings = []
                for filing in filings[:20]:  # Limit to recent filings
                    try:
                        filing_date = filing.filing_date
                        if isinstance(filing_date, str):
                            filing_date = datetime.strptime(filing_date, '%Y-%m-%d')
                        if filing_date >= start_date:
                            filtered_filings.append(filing)
                    except:
                        continue
                filings = filtered_filings[:10]  # Limit to 10 most recent
            
            print(f"Found {len(filings)} filings for {ticker}")
            
            if not filings:
                print(f"  ⚠ No filings found for {ticker}")
                return False
            
            # Create ticker directory in raw data
            ticker_raw_dir = Path(RAW_DATA_DIR) / ticker
            ticker_raw_dir.mkdir(exist_ok=True)
            
            # Process each filing
            processed_filings = []
            for i, filing in enumerate(filings[:10]):  # Limit to 10 filings
                try:
                    filing_data = self.process_filing(filing, company, ticker)
                    if filing_data:
                        processed_filings.append(filing_data)
                        
                        # Save individual filing to raw directory
                        filing_filename = f"{filing_data['form']}_{filing_data['date']}_{filing_data['accession_number']}.json"
                        filing_path = ticker_raw_dir / filing_filename
                        
                        with open(filing_path, 'w') as f:
                            json.dump(filing_data, f, indent=2)
                        
                        print(f"  ✓ Saved {filing_data['form']} filing from {filing_data['date']}")
                        
                except Exception as e:
                    print(f"  ⚠ Error processing filing {i+1}: {e}")
                    continue
            
            if processed_filings:
                # Generate timeline and summary
                self.generate_timeline_and_summary(ticker, processed_filings)
                print(f"✓ Completed {ticker} ({len(processed_filings)} filings processed)")
                return True
            else:
                print(f"✗ No filings could be processed for {ticker}")
                return False
                
        except Exception as e:
            print(f"✗ Error processing ticker {ticker}: {e}")
            return False
    
    def process_filing(self, filing, company, ticker: str) -> Dict[str, Any]:
        """Process individual filing and extract metadata"""
        try:
            # Extract filing information with safe attribute access
            filing_date = str(filing.filing_date) if hasattr(filing, 'filing_date') else ""
            form = str(filing.form) if hasattr(filing, 'form') else "Unknown"
            accession = str(filing.accession_number) if hasattr(filing, 'accession_number') else ""
            
            filing_data = {
                "ticker": ticker,
                "form": form,
                "date": filing_date,
                "type": form,
                "accession_number": accession,
                "company_name": str(company.name) if hasattr(company, 'name') else ticker,
                "filing_url": str(filing.filing_details_url) if hasattr(filing, 'filing_details_url') else "",
                "processed_at": datetime.now().isoformat()
            }
            
            # Try to get filing text for summary
            try:
                if hasattr(filing, 'text') and callable(filing.text):
                    filing_text = filing.text()[:5000]  # First 5000 characters
                    filing_data["text_preview"] = filing_text
            except:
                filing_data["text_preview"] = "Text extraction not available"
            
            return filing_data
            
        except Exception as e:
            print(f"    ⚠ Error extracting filing data: {e}")
            return None
    
    def generate_timeline_and_summary(self, ticker: str, filings: List[Dict[str, Any]]):
        """Generate timeline and summary using DeepSeek API"""
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your_deepseek_api_key_here":
            print(f"  ⚠ DeepSeek API key not configured. Skipping AI summary for {ticker}")
            self.create_basic_timeline(ticker, filings)
            return
        
        try:
            # Prepare data for AI analysis
            filings_summary = []
            for filing in filings:
                filings_summary.append({
                    "form": filing["form"],
                    "date": filing["date"],
                    "text_preview": filing.get("text_preview", "No preview available")
                })
            
            # Create AI prompt
            prompt = f"""
Analyze the following SEC filings for {ticker} and create:
1. A timeline of key events in bullet points
2. A comprehensive summary of the company's recent activities

Filings data:
{json.dumps(filings_summary, indent=2)}

Please provide:
- Timeline: Key events in chronological order (bullet points)
- Summary: Overall analysis of company performance and developments
"""
            
            # Call DeepSeek API
            response = self.call_deepseek_api(prompt)
            
            if response:
                # Save AI-generated timeline and summary
                processed_dir = Path(PROCESSED_DATA_DIR) / ticker
                processed_dir.mkdir(exist_ok=True)
                
                ai_analysis = {
                    "ticker": ticker,
                    "generated_at": datetime.now().isoformat(),
                    "filings_analyzed": len(filings),
                    "ai_timeline": response,
                    "filings_metadata": [{
                        "form": f["form"],
                        "date": f["date"],
                        "accession": f["accession_number"]
                    } for f in filings]
                }
                
                with open(processed_dir / "timeline_summary.json", 'w') as f:
                    json.dump(ai_analysis, f, indent=2)
                
                print(f"  ✓ Generated AI timeline and summary for {ticker}")
            else:
                self.create_basic_timeline(ticker, filings)
                
        except Exception as e:
            print(f"  ⚠ Error generating AI summary for {ticker}: {e}")
            self.create_basic_timeline(ticker, filings)
    
    def create_basic_timeline(self, ticker: str, filings: List[Dict[str, Any]]):
        """Create basic timeline without AI"""
        processed_dir = Path(PROCESSED_DATA_DIR) / ticker
        processed_dir.mkdir(exist_ok=True)
        
        # Sort filings by date
        sorted_filings = sorted(filings, key=lambda x: x["date"], reverse=True)
        
        timeline_events = []
        for filing in sorted_filings:
            timeline_events.append(f"• {filing['date']}: Filed {filing['form']} - {filing['company_name']}")
        
        basic_analysis = {
            "ticker": ticker,
            "generated_at": datetime.now().isoformat(),
            "filings_analyzed": len(filings),
            "basic_timeline": timeline_events,
            "summary": f"Analysis of {len(filings)} recent SEC filings for {ticker}. AI summary not available.",
            "filings_metadata": [{
                "form": f["form"],
                "date": f["date"],
                "accession": f["accession_number"]
            } for f in filings]
        }
        
        with open(processed_dir / "timeline_summary.json", 'w') as f:
            json.dump(basic_analysis, f, indent=2)
        
        print(f"  ✓ Generated basic timeline for {ticker}")
    
    def call_deepseek_api(self, prompt: str) -> str:
        """Call DeepSeek API for analysis"""
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1500,
                "temperature": 0.7
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"    ⚠ DeepSeek API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"    ⚠ Error calling DeepSeek API: {e}")
            return None
    
    def run(self):
        """Main execution method"""
        print("SEC Filing Data Download Script")
        print("=" * 40)
        
        # Check if edgartools is available
        if not self.setup_edgar_identity():
            print("\n⚠ Cannot proceed without edgartools. Please install it first.")
            return
        
        # Load tickers
        tickers = self.load_tickers()
        
        if not tickers:
            print("⚠ No tickers to process")
            return
        
        # Process each ticker
        successful = 0
        for ticker in tickers:
            if self.download_filings_for_ticker(ticker):
                successful += 1
        
        print("\n" + "=" * 40)
        print(f"Download completed! {successful}/{len(tickers)} tickers processed successfully")
        print(f"Raw data saved in '{RAW_DATA_DIR}' directory")
        print(f"Processed data saved in '{PROCESSED_DATA_DIR}' directory")
        print("\nTo use with SECChronicle app:")
        print("1. Start the backend: python backend/main.py")
        print("2. Start the frontend: cd frontend && npm run dev")
        print("3. Open http://localhost:5173")

def main():
    """Main function"""
    downloader = SECDataDownloader()
    downloader.run()

if __name__ == "__main__":
    main()