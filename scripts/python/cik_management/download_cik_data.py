#!/usr/bin/env python3
"""
EDGAR CIK Data Downloader

This script downloads all company CIK (Central Index Key) numbers from the SEC EDGAR database
and saves them locally with company ticker, name, and CIK information.

The SEC provides a JSON file with all company tickers and their corresponding CIK numbers.
This data is updated regularly by the SEC.

Usage:
    python download_cik_data.py

Output:
    - data/cik_database/company_tickers.json (raw SEC data)
    - data/cik_database/cik_database.csv (processed CSV format)
    - data/cik_database/cik_database.json (processed JSON format)
"""

import json
import csv
import requests
import os
from datetime import datetime
from pathlib import Path
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cik_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CIKDownloader:
    def __init__(self, data_dir="../../../data/cik_database"):
        """
        Initialize the CIK downloader.
        
        Args:
            data_dir (str): Directory to save the downloaded data
        """
        self.data_dir = Path(__file__).parent / data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # SEC EDGAR company tickers endpoint
        self.sec_url = "https://www.sec.gov/files/company_tickers.json"
        
        # Set headers to comply with SEC requirements
        self.headers = {
            'User-Agent': 'Edgar-Insights-Tool contact@example.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
    
    def download_raw_data(self):
        """
        Download the raw company tickers JSON from SEC EDGAR.
        
        Returns:
            dict: Raw company data from SEC
        """
        logger.info("Downloading company tickers from SEC EDGAR...")
        
        try:
            # Add delay to be respectful to SEC servers
            time.sleep(0.1)
            
            response = requests.get(self.sec_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Save raw data
            raw_file = self.data_dir / "company_tickers.json"
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Raw data saved to {raw_file}")
            logger.info(f"Downloaded {len(data)} company records")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading data from SEC: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            raise
    
    def process_data(self, raw_data):
        """
        Process the raw SEC data into a more usable format.
        
        Args:
            raw_data (dict): Raw data from SEC
            
        Returns:
            list: Processed company data
        """
        logger.info("Processing company data...")
        
        processed_data = []
        
        for key, company_info in raw_data.items():
            if isinstance(company_info, dict):
                processed_record = {
                    'ticker': company_info.get('ticker', '').upper(),
                    'company_name': company_info.get('title', ''),
                    'cik': str(company_info.get('cik_str', '')).zfill(10),  # Pad with zeros to 10 digits
                    'cik_raw': company_info.get('cik_str', ''),
                    'last_updated': datetime.now().isoformat()
                }
                processed_data.append(processed_record)
        
        # Sort by ticker for easier lookup
        processed_data.sort(key=lambda x: x['ticker'])
        
        logger.info(f"Processed {len(processed_data)} company records")
        return processed_data
    
    def save_processed_data(self, processed_data):
        """
        Save processed data in both CSV and JSON formats.
        
        Args:
            processed_data (list): Processed company data
        """
        # Save as JSON
        json_file = self.data_dir / "cik_database.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'total_companies': len(processed_data),
                    'last_updated': datetime.now().isoformat(),
                    'source': 'SEC EDGAR company_tickers.json'
                },
                'companies': processed_data
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON data saved to {json_file}")
        
        # Save as CSV
        csv_file = self.data_dir / "cik_database.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if processed_data:
                fieldnames = processed_data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(processed_data)
        
        logger.info(f"CSV data saved to {csv_file}")
    
    def create_summary_report(self, processed_data):
        """
        Create a summary report of the downloaded data.
        
        Args:
            processed_data (list): Processed company data
        """
        summary = {
            'total_companies': len(processed_data),
            'companies_with_tickers': len([c for c in processed_data if c['ticker']]),
            'companies_without_tickers': len([c for c in processed_data if not c['ticker']]),
            'download_timestamp': datetime.now().isoformat(),
            'sample_companies': processed_data[:5] if processed_data else []
        }
        
        summary_file = self.data_dir / "download_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Summary report saved to {summary_file}")
        logger.info(f"Total companies: {summary['total_companies']}")
        logger.info(f"Companies with tickers: {summary['companies_with_tickers']}")
        logger.info(f"Companies without tickers: {summary['companies_without_tickers']}")
    
    def run(self):
        """
        Main execution method to download and process CIK data.
        """
        try:
            logger.info("Starting CIK data download process...")
            
            # Download raw data
            raw_data = self.download_raw_data()
            
            # Process data
            processed_data = self.process_data(raw_data)
            
            # Save processed data
            self.save_processed_data(processed_data)
            
            # Create summary report
            self.create_summary_report(processed_data)
            
            logger.info("CIK data download completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during CIK data download: {e}")
            raise

def main():
    """
    Main function to run the CIK downloader.
    """
    downloader = CIKDownloader()
    downloader.run()

if __name__ == "__main__":
    main()