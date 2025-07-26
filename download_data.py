#!/usr/bin/env python3
"""
SEC Filing Data Download Script for SECChronicle
Downloads SEC filings and organizes them into folder structure
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DATA_DIR = "data"
RAW_DATA_DIR = "data/raw"
TICKERS_FILE = "tickers.json"
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
            
            # Get filings with enhanced error handling for pyarrow
            try:
                # Try to get filings without date filter first to avoid pyarrow issues
                all_filings = company.get_filings(form=['10-K', '10-Q', '8-K', 'DEF 14A'])
                
                # Convert to list safely
                filings_list = []
                try:
                    # Try to iterate through filings safely
                    for i, filing in enumerate(all_filings):
                        if i >= 20:  # Limit to first 20 to avoid memory issues
                            break
                        filings_list.append(filing)
                except Exception as iter_error:
                    print(f"  ⚠ Error iterating filings: {iter_error}")
                    # Try alternative access method
                    try:
                        if hasattr(all_filings, 'to_pandas'):
                            df = all_filings.to_pandas()
                            filings_list = df.head(20).to_dict('records')
                        elif hasattr(all_filings, '__len__') and len(all_filings) > 0:
                            # Try direct indexing
                            for i in range(min(20, len(all_filings))):
                                try:
                                    filings_list.append(all_filings[i])
                                except:
                                    break
                    except Exception as alt_error:
                        print(f"  ⚠ Alternative access failed: {alt_error}")
                        filings_list = []
                
                # Filter by date manually if we have filings
                filtered_filings = []
                for filing in filings_list:
                    try:
                        # Try to extract date safely
                        filing_date = None
                        if hasattr(filing, 'filing_date'):
                            date_val = filing.filing_date
                            if hasattr(date_val, 'to_pylist'):
                                date_list = date_val.to_pylist()
                                filing_date = date_list[0] if date_list else None
                            else:
                                filing_date = date_val
                        
                        if filing_date:
                            if isinstance(filing_date, str):
                                filing_date = datetime.strptime(filing_date, '%Y-%m-%d')
                            if filing_date >= start_date:
                                filtered_filings.append(filing)
                                if len(filtered_filings) >= 10:
                                    break
                    except Exception as date_error:
                        print(f"    ⚠ Error processing filing date: {date_error}")
                        # Include filing anyway if we can't check date
                        filtered_filings.append(filing)
                        if len(filtered_filings) >= 10:
                            break
                
                filings = filtered_filings[:10]  # Limit to 10 most recent
                
            except Exception as e:
                print(f"  ⚠ Error getting filings: {e}")
                filings = []
            
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
                # Generate basic timeline
                self.create_basic_timeline(ticker, processed_filings)
                print(f"✓ Completed {ticker} ({len(processed_filings)} filings processed)")
                return True
            else:
                print(f"✗ No filings could be processed for {ticker}")
                return False
                
        except Exception as e:
            print(f"✗ Error processing ticker {ticker}: {e}")
            return False
    
    def process_filing(self, filing, company, ticker: str) -> Dict[str, Any]:
        """Process individual filing and extract metadata with pyarrow compatibility"""
        try:
            # Use safer attribute extraction to avoid pyarrow issues
            filing_data = {
                "ticker": ticker,
                "form": "Unknown",
                "date": "",
                "type": "Unknown",
                "accession_number": "",
                "company_name": ticker,
                "filing_url": "",
                "processed_at": datetime.now().isoformat(),
                "text_preview": "Text extraction not available"
            }
            
            # Try multiple methods to extract filing information
            try:
                # Method 1: Direct string conversion
                if hasattr(filing, 'form'):
                    form_val = filing.form
                    if hasattr(form_val, 'to_pylist'):
                        # Handle pyarrow array
                        form_list = form_val.to_pylist()
                        filing_data["form"] = str(form_list[0]) if form_list else "Unknown"
                    else:
                        filing_data["form"] = str(form_val)
                    filing_data["type"] = filing_data["form"]
            except Exception as e:
                print(f"    ⚠ Error extracting form: {e}")
            
            try:
                if hasattr(filing, 'filing_date'):
                    date_val = filing.filing_date
                    if hasattr(date_val, 'to_pylist'):
                        # Handle pyarrow array
                        date_list = date_val.to_pylist()
                        filing_data["date"] = str(date_list[0]) if date_list else ""
                    else:
                        filing_data["date"] = str(date_val)
            except Exception as e:
                print(f"    ⚠ Error extracting date: {e}")
            
            try:
                if hasattr(filing, 'accession_number'):
                    acc_val = filing.accession_number
                    if hasattr(acc_val, 'to_pylist'):
                        # Handle pyarrow array
                        acc_list = acc_val.to_pylist()
                        filing_data["accession_number"] = str(acc_list[0]) if acc_list else ""
                    else:
                        filing_data["accession_number"] = str(acc_val)
            except Exception as e:
                print(f"    ⚠ Error extracting accession: {e}")
            
            try:
                if hasattr(company, 'name'):
                    name_val = company.name
                    if hasattr(name_val, 'to_pylist'):
                        # Handle pyarrow array
                        name_list = name_val.to_pylist()
                        filing_data["company_name"] = str(name_list[0]) if name_list else ticker
                    else:
                        filing_data["company_name"] = str(name_val)
            except Exception as e:
                print(f"    ⚠ Error extracting company name: {e}")
            
            try:
                if hasattr(filing, 'filing_details_url'):
                    url_val = filing.filing_details_url
                    if hasattr(url_val, 'to_pylist'):
                        # Handle pyarrow array
                        url_list = url_val.to_pylist()
                        filing_data["filing_url"] = str(url_list[0]) if url_list else ""
                    else:
                        filing_data["filing_url"] = str(url_val)
            except Exception as e:
                print(f"    ⚠ Error extracting URL: {e}")
            
            # Alternative method: Try to convert filing to dict if available
            try:
                if hasattr(filing, 'to_dict'):
                    filing_dict = filing.to_dict()
                    filing_data.update({
                        "form": str(filing_dict.get('form', filing_data["form"])),
                        "date": str(filing_dict.get('filing_date', filing_data["date"])),
                        "accession_number": str(filing_dict.get('accession_number', filing_data["accession_number"])),
                        "company_name": str(filing_dict.get('company_name', filing_data["company_name"]))
                    })
                    filing_data["type"] = filing_data["form"]
            except Exception as e:
                print(f"    ⚠ Error with to_dict method: {e}")
            
            # Skip text extraction to avoid additional pyarrow issues
            
            return filing_data
            
        except Exception as e:
            print(f"    ⚠ Error extracting filing data: {e}")
            return None
    
    def create_basic_timeline(self, ticker: str, filings: List[Dict[str, Any]]):
        """Create basic timeline without AI"""
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
            "summary": f"Analysis of {len(filings)} recent SEC filings for {ticker}.",
            "filings_metadata": [{
                "form": f["form"],
                "date": f["date"],
                "accession": f["accession_number"]
            } for f in filings]
        }
        
        # Save to raw data directory instead of processed
        ticker_dir = Path(RAW_DATA_DIR) / ticker
        ticker_dir.mkdir(exist_ok=True)
        
        with open(ticker_dir / "timeline_summary.json", 'w') as f:
            json.dump(basic_analysis, f, indent=2)
        
        print(f"  ✓ Generated basic timeline for {ticker}")
    

    
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