#!/usr/bin/env python3
"""
SEC Filing Downloader using sec-edgar-downloader library
Downloads SEC filings for specified tickers and organizes them in data/raw directory.
"""

import os
import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from sec_edgar_downloader import Downloader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SECDownloader:
    def __init__(self):
        # Get configuration from environment variables
        self.company_name = os.getenv('COMPANY_NAME', 'Your Company Name')
        self.email = os.getenv('EMAIL', 'your.email@example.com')
        
        # Set up directories (adjust path since script is now in scripts/python/)
        self.base_dir = Path(__file__).parent.parent.parent
        self.raw_data_dir = self.base_dir / 'data' / 'raw'
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize downloader
        self.downloader = Downloader(self.company_name, self.email)
        
        # Date range for filings (last 6 months)
        self.end_date = datetime.now().date()
        self.start_date = self.end_date - timedelta(days=180)
        
        print(f"📊 SEC Filing Downloader initialized")
        print(f"📅 Date range: {self.start_date} to {self.end_date}")
        print(f"📁 Raw data directory: {self.raw_data_dir}")
    
    def load_tickers(self):
        """Load ticker symbols from tickers.json"""
        tickers_file = self.base_dir / 'tickers.json'
        try:
            with open(tickers_file, 'r') as f:
                tickers = json.load(f)
            print(f"✅ Loaded {len(tickers)} tickers: {', '.join(tickers)}")
            return tickers
        except FileNotFoundError:
            print(f"❌ Error: {tickers_file} not found")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing {tickers_file}: {e}")
            return []
    
    def check_existing_data(self, ticker):
        """Check if data already exists for a ticker"""
        ticker_dir = self.raw_data_dir / ticker
        if not ticker_dir.exists():
            return False
        
        # Check if there are any JSON files (excluding timeline_summary.json)
        json_files = [f for f in ticker_dir.glob('*.json') if f.name != 'timeline_summary.json']
        
        if json_files:
            print(f"📁 Data already exists for {ticker} ({len(json_files)} filings found)")
            return True
        return False
    
    def download_filings_for_ticker(self, ticker, force_download=False):
        """Download filings for a specific ticker"""
        print(f"\nProcessing ticker: {ticker}")
        
        # Check if data already exists
        if not force_download and self.check_existing_data(ticker):
            print(f"⏭️  Skipping {ticker} - data already downloaded")
            return 0
        
        ticker_dir = self.raw_data_dir / ticker
        ticker_dir.mkdir(exist_ok=True)
        
        # Download different types of filings - comprehensive list
        filing_types = [
            '10-K',      # Annual Report
            '10-Q',      # Quarterly Report
            '8-K',       # Current Report
            'DEF 14A',   # Proxy Statement
            '10-K/A',    # Annual Report Amendment
            '10-Q/A',    # Quarterly Report Amendment
            '8-K/A',     # Current Report Amendment
            'S-1',       # Registration Statement
            'S-3',       # Registration Statement
            'S-4',       # Registration Statement
            'S-8',       # Registration Statement for Employee Stock Plans
            'F-1',       # Registration Statement (Foreign)
            'F-3',       # Registration Statement (Foreign)
            'F-4',       # Registration Statement (Foreign)
            '20-F',      # Annual Report (Foreign)
            '40-F',      # Annual Report (Foreign)
            '6-K',       # Report of Foreign Private Issuer
            'SC 13D',    # Beneficial Ownership Report
            'SC 13G',    # Beneficial Ownership Report
            'SC 13D/A',  # Beneficial Ownership Report Amendment
            'SC 13G/A',  # Beneficial Ownership Report Amendment
            '3',         # Initial Statement of Beneficial Ownership
            '4',         # Statement of Changes in Beneficial Ownership
            '5',         # Annual Statement of Changes in Beneficial Ownership
            '11-K',      # Annual Report of Employee Stock Purchase Plans
            'NT 10-K',   # Notification of Late Filing
            'NT 10-Q',   # Notification of Late Filing
            'NT 20-F',   # Notification of Late Filing
            'DEFA14A',   # Additional Proxy Soliciting Materials
            'PRER14A',   # Preliminary Proxy Statement
            'DEFR14A',   # Definitive Proxy Statement
            'PREC14A',   # Preliminary Proxy Statement
            'DEFC14A',   # Definitive Proxy Statement
            'PRE 14A',   # Preliminary Proxy Statement
            'DEFM14A',   # Definitive Proxy Statement
            'PREM14A',   # Preliminary Proxy Statement
            'DEFN14A',   # Definitive Proxy Statement
            'PREN14A',   # Preliminary Proxy Statement
            'DEFR14C',   # Definitive Information Statement
            'PRER14C',   # Preliminary Information Statement
            'DEF 14C',   # Definitive Information Statement
            'PRE 14C',   # Preliminary Information Statement
            'DFRN14A',   # Definitive Additional Materials
            'DFAN14A',   # Definitive Additional Materials
            'PRRN14A',   # Preliminary Additional Materials
            'PRFN14A',   # Preliminary Additional Materials
            'PRAN14A',   # Preliminary Additional Materials
            'PRFN14A',   # Preliminary Additional Materials
            'UPLOAD',    # Correspondence
            'CORRESP',   # Correspondence
            'COVER',     # Cover Page
            'EX-99',     # Additional Exhibits
            'EX-101',    # XBRL Instance Document
            'EX-32',     # Section 302 Certification
            'EX-31',     # Section 302 Certification
            'EFFECT',    # Notice of Effectiveness
            'POS AM',    # Post-Effective Amendment
            'POS 462B',  # Post-Effective Amendment
            'POS 462C',  # Post-Effective Amendment
            'POSAM',     # Post-Effective Amendment
            'RW',        # Registration Withdrawal
            'RW WD',     # Registration Withdrawal
            'SUPPL',     # Supplement to Prospectus
            '424B1',     # Prospectus
            '424B2',     # Prospectus
            '424B3',     # Prospectus
            '424B4',     # Prospectus
            '424B5',     # Prospectus
            '424B7',     # Prospectus
            '424B8',     # Prospectus
            '497',       # Definitive Materials
            '497AD',     # Definitive Materials
            '497J',      # Certification of No Change
            '497K',      # Summary Prospectus
            'N-1A',      # Registration Statement (Investment Company)
            'N-2',       # Registration Statement (Closed-End Investment Company)
            'N-3',       # Registration Statement (Separate Account)
            'N-4',       # Registration Statement (Variable Annuity)
            'N-5',       # Registration Statement (Small Business Investment Company)
            'N-6',       # Registration Statement (Unit Investment Trust)
            'N-8A',      # Notification of Registration
            'N-8B-2',    # Registration Statement (Unit Investment Trust)
            'N-14',      # Registration Statement (Investment Company)
            'N-18F1',    # Notification of Election
            'N-23C3A',   # Notification of Periodic Repurchase Offer
            'N-23C3B',   # Notification of Periodic Repurchase Offer
            'N-23C3C',   # Notification of Periodic Repurchase Offer
            'N-27D-1',   # Accounting for Deferred Charges
            'N-30B-2',   # Periodic Report
            'N-30D',     # Annual Report
            'N-CSR',     # Certified Shareholder Report
            'N-CSRS',    # Semi-Annual Report
            'N-Q',       # Quarterly Schedule of Portfolio Holdings
            'N-PX',      # Annual Report of Proxy Voting Record
            'N-CEN',     # Annual Report for Registered Investment Companies
            'ADV',       # Investment Adviser Registration
            'ADV-E',     # Investment Adviser Registration
            'ADV-H',     # Investment Adviser Registration
            'ADV-NR',    # Investment Adviser Registration
            'ADV-W',     # Investment Adviser Registration
            'PF',        # Private Fund Report
            'ABS-EE',    # Asset-Backed Securities
            'ABS-15G',   # Asset-Backed Securities
            'CFPORTAL',  # Funding Portal Report
            'CRS',       # Customer Relationship Summary
            'CUSTODY',   # Custody Report
            'MSD',       # Municipal Securities Dealer Report
            'MSDW',      # Municipal Securities Dealer Withdrawal
            'X-17A-5',   # Financial and Operational Combined Uniform Single Report
            'ATS',       # Alternative Trading System
            'ATS-N',     # Alternative Trading System
            'ATS-R',     # Alternative Trading System
            'BD',        # Broker-Dealer Registration
            'BD-N',      # Broker-Dealer Registration
            'BDW',       # Broker-Dealer Withdrawal
            'SBS',       # Security-Based Swap
            'SBSE',      # Security-Based Swap Execution Facility
            'SBSE-A',    # Security-Based Swap Execution Facility
            'SBSE-BD',   # Security-Based Swap Execution Facility
            'SBSE-C',    # Security-Based Swap Execution Facility
            'SDR',       # Security-Based Swap Data Repository
            'TA-1',      # Transfer Agent Registration
            'TA-2',      # Transfer Agent Registration
            'TA-W',      # Transfer Agent Withdrawal
            'ID',        # Information Document
            'MA',        # Municipal Advisor Registration
            'MA-I',      # Municipal Advisor Registration
            'MA-NR',     # Municipal Advisor Registration
            'MA-W',      # Municipal Advisor Withdrawal
            'NRSRO',     # Nationally Recognized Statistical Rating Organization
            'PILOT',     # Pilot Program Report
            'REP',       # Regulatory Report
            'SCI',       # Systems Compliance and Integrity
            'TCR',       # Tip, Complaint or Referral
            'TH',        # Temporary Hardship Exemption
            'WB-APP',    # Whistleblower Application
            'WB-DEC',    # Whistleblower Declaration
        ]
        total_filings = 0
        
        for filing_type in filing_types:
            try:
                print(f"  📄 Downloading {filing_type} filings...")
                
                # Create a downloader instance for this specific download location
                temp_dir = ticker_dir / 'temp'
                temp_dir.mkdir(exist_ok=True)
                
                # Create downloader with specific download folder
                downloader = Downloader(self.company_name, self.email, str(temp_dir))
                
                # Use sec-edgar-downloader to get filings
                filings_count = downloader.get(
                    filing_type,
                    ticker,
                    after=self.start_date.strftime('%Y-%m-%d'),
                    before=self.end_date.strftime('%Y-%m-%d'),
                    limit=10  # Limit to 10 most recent filings
                )
                
                if filings_count > 0:
                    # Process downloaded files
                    self.process_downloaded_files(temp_dir, ticker_dir, filing_type)
                    total_filings += filings_count
                    print(f"    ✅ Downloaded {filings_count} {filing_type} filings")
                else:
                    print(f"    ℹ️  No {filing_type} filings found")
                
                # Clean up temp directory
                import shutil
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                
                # Add 1 second sleep between filing type extractions
                time.sleep(1)
                    
            except Exception as e:
                print(f"    ⚠️  Error downloading {filing_type}: {e}")
                # Add sleep even on error to avoid overwhelming the server
                time.sleep(1)
        
        if total_filings > 0:
            # Create timeline summary
            self.create_timeline_summary(ticker_dir, ticker)
            print(f"✅ Completed {ticker} ({total_filings} filings processed)")
        else:
            print(f"⚠️  No filings found for {ticker}")
        
        return total_filings
    
    def process_downloaded_files(self, temp_dir, ticker_dir, filing_type):
        """Process files downloaded by sec-edgar-downloader"""
        # sec-edgar-downloader creates a structure like: temp_dir/sec-edgar-filings/TICKER/FILING_TYPE/
        edgar_dir = temp_dir / 'sec-edgar-filings'
        if not edgar_dir.exists():
            return
        
        # Find the ticker directory
        for ticker_folder in edgar_dir.iterdir():
            if ticker_folder.is_dir():
                filing_type_dir = ticker_folder / filing_type
                if filing_type_dir.exists():
                    # Process each filing
                    for filing_dir in filing_type_dir.iterdir():
                        if filing_dir.is_dir():
                            self.convert_filing_to_json(filing_dir, ticker_dir, filing_type)
    
    def convert_filing_to_json(self, filing_dir, ticker_dir, filing_type):
        """Convert downloaded filing to our JSON format"""
        try:
            # Get filing metadata from directory name
            # Format is usually: ACCESSION-NUMBER
            accession_number = filing_dir.name
            
            # Look for the main filing file (usually .txt or .htm)
            filing_files = list(filing_dir.glob('*.txt')) + list(filing_dir.glob('*.htm'))
            if not filing_files:
                return
            
            main_file = filing_files[0]
            
            # Extract date from accession number or use current date
            try:
                # Accession format: XXXXXXXXXX-XX-XXXXXX
                date_part = accession_number.split('-')[1]
                filing_date = f"20{date_part[:2]}-{date_part[2:4]}-{date_part[4:6]}"
            except:
                filing_date = datetime.now().strftime('%Y-%m-%d')
            
            # Read filing content
            try:
                with open(main_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except:
                content = "Content could not be read"
            
            # Create our JSON structure
            filing_data = {
                "form": filing_type,
                "filing_date": filing_date,
                "accession_number": accession_number,
                "company_name": "Company Name",  # Will be updated if available
                "filing_url": f"https://www.sec.gov/Archives/edgar/data/{accession_number}",
                "content": content[:10000] if len(content) > 10000 else content  # Limit content size
            }
            
            # Save as JSON file
            json_filename = f"{filing_type}_{filing_date}_{accession_number}.json"
            json_path = ticker_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(filing_data, f, indent=2, ensure_ascii=False)
            
            print(f"    ✅ Saved {filing_type} filing from {filing_date}")
            
        except Exception as e:
            print(f"    ⚠️  Error processing filing {filing_dir.name}: {e}")
    
    def create_timeline_summary(self, ticker_dir, ticker):
        """Create timeline_summary.json file"""
        try:
            # Get all JSON files in the ticker directory
            json_files = list(ticker_dir.glob('*.json'))
            
            filings = []
            for json_file in json_files:
                if json_file.name == 'timeline_summary.json':
                    continue
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        filing_data = json.load(f)
                    
                    filings.append({
                        "form": filing_data.get("form", "Unknown"),
                        "filing_date": filing_data.get("filing_date", "Unknown"),
                        "accession_number": filing_data.get("accession_number", "Unknown"),
                        "company_name": filing_data.get("company_name", ticker),
                        "filing_url": filing_data.get("filing_url", ""),
                        "summary": f"SEC {filing_data.get('form', 'Filing')} filed on {filing_data.get('filing_date', 'Unknown date')}",
                        "ai_timeline": f"{filing_data.get('filing_date', 'Unknown')}: {filing_data.get('form', 'Filing')} submitted"
                    })
                except Exception as e:
                    print(f"    ⚠️  Error reading {json_file.name}: {e}")
            
            # Sort by filing date
            filings.sort(key=lambda x: x.get('filing_date', ''), reverse=True)
            
            # Create timeline summary
            timeline_summary = {
                "ticker": ticker,
                "filings": filings,
                "timeline": [f["ai_timeline"] for f in filings],
                "summary": f"Downloaded {len(filings)} SEC filings for {ticker}"
            }
            
            # Save timeline summary
            timeline_path = ticker_dir / 'timeline_summary.json'
            with open(timeline_path, 'w', encoding='utf-8') as f:
                json.dump(timeline_summary, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ Generated timeline summary for {ticker}")
            
        except Exception as e:
            print(f"  ⚠️  Error creating timeline summary: {e}")
    
    def run(self):
        """Main execution method"""
        print("🚀 Starting SEC filing download...\n")
        
        # Load tickers
        tickers = self.load_tickers()
        if not tickers:
            print("❌ No tickers to process")
            return
        
        # Check for force download flag
        force_download = '--force' in sys.argv or '-f' in sys.argv
        if force_download:
            print("⚠️  Force download mode enabled - will re-download existing data\n")
        
        # Process each ticker
        successful_tickers = 0
        for ticker in tickers:
            try:
                filings_count = self.download_filings_for_ticker(ticker, force_download)
                if filings_count > 0:
                    successful_tickers += 1
            except Exception as e:
                print(f"❌ Error processing {ticker}: {e}")
        
        print("\n" + "="*50)
        print(f"Download completed! {successful_tickers}/{len(tickers)} tickers processed successfully")
        print(f"Raw data saved in '{self.raw_data_dir}' directory")
        print("\nTo use with SECChronicle app:")
        print("1. Start the backend: python backend/main.py")
        print("2. Start the frontend: cd frontend && npm run dev")
        print("3. Open http://localhost:5173")

if __name__ == "__main__":
    downloader = SECDownloader()
    downloader.run()