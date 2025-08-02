#!/usr/bin/env python3
"""
SEC Submissions Data Downloader

This script downloads SEC submissions data from the SEC's API for a given CIK.
The data includes filing history, company metadata, and other submission information.

Usage:
    python download_sec_submissions.py --cik 0002012383
    python download_sec_submissions.py --cik 0002012383 --output-dir data/submissions
"""

import argparse
import json
import os
import requests
import time
from pathlib import Path
from typing import Dict, Any


class SECSubmissionsDownloader:
    """Downloads SEC submissions data for specified CIKs."""
    
    def __init__(self, output_dir: str = "data/submissions"):
        self.output_dir = Path(output_dir)
        self.base_url = "https://data.sec.gov/submissions"
        # SEC requires a User-Agent header
        self.headers = {
            "User-Agent": "Edgar Insights Tool admin@example.com",
            "Accept": "application/json"
        }
        
    def download_submissions(self, cik: str) -> Dict[str, Any]:
        """Download submissions data for a given CIK.
        
        Args:
            cik: 10-digit CIK with leading zeros
            
        Returns:
            Dictionary containing the submissions data
        """
        # Ensure CIK is 10 digits with leading zeros
        cik = cik.zfill(10)
        
        url = f"{self.base_url}/CIK{cik}.json"
        print(f"Downloading submissions data for CIK {cik}...")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            print(f"Successfully downloaded data for CIK {cik}")
            print(f"Company: {data.get('name', 'Unknown')}")
            print(f"Entity Type: {data.get('entityType', 'Unknown')}")
            print(f"SIC: {data.get('sic', 'Unknown')} - {data.get('sicDescription', 'Unknown')}")
            
            # Print some basic stats about filings
            filings = data.get('filings', {}).get('recent', {})
            if filings:
                num_filings = len(filings.get('accessionNumber', []))
                print(f"Number of recent filings: {num_filings}")
                
                # Show some recent form types
                form_types = filings.get('form', [])
                if form_types:
                    unique_forms = list(set(form_types[:20]))  # Show first 20 unique forms
                    print(f"Recent form types: {', '.join(unique_forms)}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Error downloading data for CIK {cik}: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response for CIK {cik}: {e}")
            raise
    
    def save_submissions(self, cik: str, data: Dict[str, Any]) -> str:
        """Save submissions data to file.
        
        Args:
            cik: 10-digit CIK with leading zeros
            data: Submissions data dictionary
            
        Returns:
            Path to saved file
        """
        # Ensure CIK is 10 digits with leading zeros
        cik = cik.zfill(10)
        
        # Create directory structure: data/submissions/CIK{cik}/
        cik_dir = self.output_dir / f"CIK{cik}"
        cik_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main submissions file
        output_file = cik_dir / "submissions.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved submissions data to: {output_file}")
        
        # Also save a summary file with key information
        summary = {
            "cik": cik,
            "name": data.get('name'),
            "entityType": data.get('entityType'),
            "sic": data.get('sic'),
            "sicDescription": data.get('sicDescription'),
            "stateOfIncorporation": data.get('stateOfIncorporation'),
            "stateOfIncorporationDescription": data.get('stateOfIncorporationDescription'),
            "fiscalYearEnd": data.get('fiscalYearEnd'),
            "tickers": data.get('tickers', []),
            "exchanges": data.get('exchanges', []),
            "ein": data.get('ein'),
            "description": data.get('description'),
            "website": data.get('website'),
            "investorWebsite": data.get('investorWebsite'),
            "category": data.get('category'),
            "phone": data.get('phone'),
            "flags": data.get('flags'),
            "formerNames": data.get('formerNames', []),
            "filings_count": len(data.get('filings', {}).get('recent', {}).get('accessionNumber', [])),
            "download_timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }
        
        summary_file = cik_dir / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"Saved summary to: {summary_file}")
        
        return str(output_file)
    
    def download_and_save(self, cik: str) -> str:
        """Download and save submissions data for a CIK.
        
        Args:
            cik: CIK (will be zero-padded to 10 digits)
            
        Returns:
            Path to saved file
        """
        data = self.download_submissions(cik)
        return self.save_submissions(cik, data)


def main():
    parser = argparse.ArgumentParser(
        description="Download SEC submissions data for a given CIK"
    )
    parser.add_argument(
        "--cik",
        required=True,
        help="Central Index Key (CIK) - will be zero-padded to 10 digits"
    )
    parser.add_argument(
        "--output-dir",
        default="data/submissions",
        help="Output directory for downloaded data (default: data/submissions)"
    )
    
    args = parser.parse_args()
    
    downloader = SECSubmissionsDownloader(args.output_dir)
    
    try:
        output_file = downloader.download_and_save(args.cik)
        print(f"\nDownload completed successfully!")
        print(f"Data saved to: {output_file}")
        
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())