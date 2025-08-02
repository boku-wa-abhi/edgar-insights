#!/usr/bin/env python3
"""
SEC Submissions Data Downloader

This script downloads SEC submissions data from the SEC's API for given CIKs.
The data includes filing history, company metadata, and other submission information.

Usage:
    # Download single CIK
    python download_sec_submissions.py --cik 0002012383
    
    # Download all CIKs from database
    python download_sec_submissions.py --bulk --cik-database data/cik_database/cik_database.json
    
    # Download with custom settings
    python download_sec_submissions.py --bulk --max-workers 5 --retry-attempts 3
"""

import argparse
import json
import os
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, List, Set
from dataclasses import dataclass
from queue import Queue
from datetime import datetime


@dataclass
class DownloadResult:
    """Result of a CIK download attempt."""
    cik: str
    success: bool
    error_message: str = ""
    file_path: str = ""
    company_name: str = ""
    attempt_count: int = 1


class SECSubmissionsDownloader:
    """Downloads SEC submissions data for specified CIKs."""
    
    def __init__(self, output_dir: str = "data/submissions", max_workers: int = 10, 
                 retry_attempts: int = 3, delay_seconds: float = 2.0):
        self.output_dir = Path(output_dir)
        self.base_url = "https://data.sec.gov/submissions"
        self.max_workers = max_workers
        self.retry_attempts = retry_attempts
        self.delay_seconds = delay_seconds
        
        # SEC requires a User-Agent header
        self.headers = {
            "User-Agent": "Edgar Insights Tool admin@example.com",
            "Accept": "application/json"
        }
        
        # Thread-safe tracking
        self.download_lock = threading.Lock()
        self.failed_ciks: Set[str] = set()
        self.completed_ciks: Set[str] = set()
        self.results: List[DownloadResult] = []
    
    def load_ciks_from_database(self, database_path: str) -> List[str]:
        """Load unique CIKs from the CIK database.
        
        Args:
            database_path: Path to the CIK database JSON file
            
        Returns:
            List of unique CIKs
        """
        try:
            with open(database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract unique CIKs from companies
            ciks = set()
            companies = data.get('companies', [])
            
            for company in companies:
                cik = company.get('cik')
                if cik:
                    ciks.add(cik)
            
            cik_list = sorted(list(ciks))
            print(f"Loaded {len(cik_list)} unique CIKs from database")
            return cik_list
            
        except Exception as e:
            print(f"Error loading CIK database: {e}")
            raise
    
    def cik_already_downloaded(self, cik: str) -> bool:
        """Check if CIK data already exists for today's date.
        
        Args:
            cik: 10-digit CIK with leading zeros
            
        Returns:
            True if data already exists for today
        """
        cik = cik.zfill(10)
        today = datetime.now().strftime('%Y%m%d')
        date_dir = self.output_dir / today
        cik_base_dir = date_dir / "CIK"
        cik_dir = cik_base_dir / cik
        submissions_file = cik_dir / "submissions.json"
        return submissions_file.exists()
        
    def download_submissions(self, cik: str, verbose: bool = True) -> Dict[str, Any]:
        """Download submissions data for a given CIK.
        
        Args:
            cik: 10-digit CIK with leading zeros
            verbose: Whether to print detailed information
            
        Returns:
            Dictionary containing the submissions data
        """
        # Ensure CIK is 10 digits with leading zeros
        cik = cik.zfill(10)
        
        url = f"{self.base_url}/CIK{cik}.json"
        if verbose:
            print(f"Downloading submissions data for CIK {cik}...")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if verbose:
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
            if verbose:
                print(f"Error downloading data for CIK {cik}: {e}")
            raise
        except json.JSONDecodeError as e:
            if verbose:
                print(f"Error parsing JSON response for CIK {cik}: {e}")
            raise
    
    def download_single_cik_with_retry(self, cik: str) -> DownloadResult:
        """Download a single CIK with retry logic and delay.
        
        Args:
            cik: CIK to download
            
        Returns:
            DownloadResult with success/failure information
        """
        cik = cik.zfill(10)
        
        # Check if already downloaded
        if self.cik_already_downloaded(cik):
            with self.download_lock:
                self.completed_ciks.add(cik)
            today = datetime.now().strftime('%Y%m%d')
            date_dir = self.output_dir / today
            cik_base_dir = date_dir / "CIK"
            cik_dir = cik_base_dir / cik
            return DownloadResult(
                cik=cik,
                success=True,
                file_path=str(cik_dir / "submissions.json"),
                company_name="Already downloaded",
                attempt_count=0
            )
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                # Add delay before download (except first attempt)
                if attempt > 1:
                    time.sleep(self.delay_seconds)
                
                # Download data
                data = self.download_submissions(cik, verbose=False)
                
                # Save data
                file_path = self.save_submissions(cik, data)
                
                # Add delay after successful download
                time.sleep(self.delay_seconds)
                
                # Track success
                with self.download_lock:
                    self.completed_ciks.add(cik)
                    if cik in self.failed_ciks:
                        self.failed_ciks.remove(cik)
                
                return DownloadResult(
                    cik=cik,
                    success=True,
                    file_path=file_path,
                    company_name=data.get('name', 'Unknown'),
                    attempt_count=attempt
                )
                
            except Exception as e:
                error_msg = str(e)
                print(f"Attempt {attempt}/{self.retry_attempts} failed for CIK {cik}: {error_msg}")
                
                if attempt == self.retry_attempts:
                    # Final failure
                    with self.download_lock:
                        self.failed_ciks.add(cik)
                    
                    return DownloadResult(
                        cik=cik,
                        success=False,
                        error_message=error_msg,
                        attempt_count=attempt
                    )
                
                # Wait before retry
                time.sleep(self.delay_seconds * attempt)  # Exponential backoff
        
        # Should not reach here
        return DownloadResult(
            cik=cik,
            success=False,
            error_message="Unknown error",
            attempt_count=self.retry_attempts
        )
    
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
        
        # Create directory structure: data/submissions/{YYYYMMDD}/CIK/{cik}/
        today = datetime.now().strftime('%Y%m%d')
        date_dir = self.output_dir / today
        cik_base_dir = date_dir / "CIK"
        cik_dir = cik_base_dir / cik
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
    
    def create_status_report(self, results: List[DownloadResult], database_path: str = None) -> str:
        """Create a status report markdown file for the download session.
        
        Args:
            results: List of download results
            database_path: Path to CIK database for getting company info
            
        Returns:
            Path to the created markdown file
        """
        today = datetime.now().strftime('%Y%m%d')
        date_dir = self.output_dir / today
        report_file = date_dir / f"{today}.md"
        
        # Count statistics
        total_folders = 0
        if date_dir.exists():
            total_folders = len([d for d in date_dir.iterdir() if d.is_dir() and d.name.startswith('CIK')])
        successful_downloads = sum(1 for r in results if r.success)
        failed_downloads = sum(1 for r in results if not r.success)
        
        # Load CIK database for company info if provided
        company_info = {}
        total_companies_in_db = 0
        if database_path and os.path.exists(database_path):
            try:
                with open(database_path, 'r') as f:
                    db_data = json.load(f)
                    total_companies_in_db = db_data.get('metadata', {}).get('total_companies', 0)
                    for company in db_data.get('companies', []):
                        cik = str(company.get('cik', '')).zfill(10)
                        company_info[cik] = {
                            'ticker': company.get('ticker', 'N/A'),
                            'name': company.get('name', 'Unknown')
                        }
            except Exception as e:
                print(f"Warning: Could not load company info from database: {e}")
        
        # Create markdown content
        content = f"# SEC Submissions Download Report - {today}\n\n"
        content += f"## Summary Statistics\n\n"
        content += f"- **Total Companies in Database**: {total_companies_in_db}\n"
        content += f"- **Total Folders Created**: {total_folders}\n"
        content += f"- **Successfully Downloaded**: {successful_downloads}\n"
        content += f"- **Failed Downloads**: {failed_downloads}\n"
        content += f"- **Download Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        
        if total_companies_in_db > 0:
            completion_rate = (total_folders / total_companies_in_db) * 100
            content += f"- **Completion Rate**: {completion_rate:.2f}%\n\n"
        
        # Create table of downloaded companies
        content += f"## Downloaded Companies\n\n"
        content += f"| CIK | Ticker | Company Name | Status |\n"
        content += f"|-----|--------|--------------|--------|\n"
        
        # Sort results by CIK for consistent ordering
        sorted_results = sorted(results, key=lambda x: x.cik)
        
        for result in sorted_results:
            if result.success:
                cik = result.cik
                ticker = company_info.get(cik, {}).get('ticker', 'N/A')
                company_name = result.company_name or company_info.get(cik, {}).get('name', 'Unknown')
                status = "✅ Downloaded"
                content += f"| {cik} | {ticker} | {company_name} | {status} |\n"
        
        # Add failed downloads section if any
        if failed_downloads > 0:
            content += f"\n## Failed Downloads\n\n"
            content += f"| CIK | Ticker | Company Name | Error |\n"
            content += f"|-----|--------|--------------|-------|\n"
            
            for result in sorted_results:
                if not result.success:
                    cik = result.cik
                    ticker = company_info.get(cik, {}).get('ticker', 'N/A')
                    company_name = result.company_name or company_info.get(cik, {}).get('name', 'Unknown')
                    error = result.error_message[:100] + "..." if len(result.error_message) > 100 else result.error_message
                    content += f"| {cik} | {ticker} | {company_name} | {error} |\n"
        
        # Write the report file
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\nStatus report created: {report_file}")
        return str(report_file)
    
    def download_and_save(self, cik: str) -> str:
        """Download and save submissions data for a given CIK.
        
        Args:
            cik: CIK to download
            
        Returns:
            Path to the saved submissions file
        """
        data = self.download_submissions(cik)
        return self.save_submissions(cik, data)
    
    def download_bulk_with_retry(self, cik_database_path: str) -> List[DownloadResult]:
        """Download submissions for all CIKs in the database with retry logic.
        
        Args:
            cik_database_path: Path to the CIK database JSON file
            
        Returns:
            List of DownloadResult objects
        """
        # Load CIKs from database
        ciks = self.load_ciks_from_database(cik_database_path)
        print(f"Found {len(ciks)} unique CIKs in database")
        
        # Filter out already downloaded CIKs
        remaining_ciks = [cik for cik in ciks if not self.cik_already_downloaded(cik)]
        print(f"Need to download {len(remaining_ciks)} CIKs (skipping {len(ciks) - len(remaining_ciks)} already downloaded)")
        
        all_results = []
        retry_round = 1
        
        while remaining_ciks:
            print(f"\n=== Download Round {retry_round} ===")
            print(f"Attempting to download {len(remaining_ciks)} CIKs with {self.max_workers} threads...")
            
            round_results = []
            
            # Use ThreadPoolExecutor for concurrent downloads
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all download tasks
                future_to_cik = {
                    executor.submit(self.download_single_cik_with_retry, cik): cik 
                    for cik in remaining_ciks
                }
                
                # Process completed downloads
                for future in as_completed(future_to_cik):
                    cik = future_to_cik[future]
                    try:
                        result = future.result()
                        round_results.append(result)
                        
                        if result.success:
                            print(f"✓ CIK {result.cik}: {result.company_name} (attempt {result.attempt_count})")
                        else:
                            print(f"✗ CIK {result.cik}: {result.error_message} (attempt {result.attempt_count})")
                            
                    except Exception as e:
                        print(f"✗ CIK {cik}: Unexpected error: {e}")
                        round_results.append(DownloadResult(
                            cik=cik,
                            success=False,
                            error_message=f"Unexpected error: {e}",
                            attempt_count=self.retry_attempts
                        ))
            
            all_results.extend(round_results)
            
            # Check for failed downloads
            failed_this_round = [r for r in round_results if not r.success]
            successful_this_round = [r for r in round_results if r.success]
            
            print(f"\nRound {retry_round} completed:")
            print(f"  Successful: {len(successful_this_round)}")
            print(f"  Failed: {len(failed_this_round)}")
            
            # Update remaining CIKs (only failed ones)
            remaining_ciks = [r.cik for r in failed_this_round]
            
            if not remaining_ciks:
                print("\n🎉 All downloads completed successfully!")
                break
            
            retry_round += 1
            print(f"\nWill retry {len(remaining_ciks)} failed CIKs in next round...")
            time.sleep(5)  # Brief pause between rounds
        
        # Final summary
        total_successful = sum(1 for r in all_results if r.success)
        total_failed = sum(1 for r in all_results if not r.success)
        
        print(f"\n=== Final Summary ===")
        print(f"Total CIKs processed: {len(ciks)}")
        print(f"Successfully downloaded: {total_successful}")
        print(f"Failed downloads: {total_failed}")
        print(f"Already existed: {len(ciks) - len([r for r in all_results if r.attempt_count > 0])}")
        
        if total_failed > 0:
            print(f"\nFailed CIKs:")
            for result in all_results:
                if not result.success:
                    print(f"  {result.cik}: {result.error_message}")
        
        # Create status report
        self.create_status_report(all_results, cik_database_path)
        
        return all_results


def main():
    """Main function to handle command line arguments and execute download."""
    parser = argparse.ArgumentParser(
        description='Download SEC submissions data for CIK(s)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download single CIK
  python download_sec_submissions.py --cik 0001018724
  
  # Download all CIKs from database
  python download_sec_submissions.py --bulk data/cik_database/cik_database.json
  
  # Bulk download with custom settings
  python download_sec_submissions.py --bulk data/cik_database/cik_database.json --workers 5 --delay 3
        """
    )
    
    # Create mutually exclusive group for single vs bulk download
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        '--cik',
        help='Single CIK (Central Index Key) - will be zero-padded to 10 digits'
    )
    
    group.add_argument(
        '--bulk',
        help='Path to CIK database JSON file for bulk download'
    )
    
    parser.add_argument(
        '--output-dir',
        default='data/submissions',
        help='Output directory for downloaded files (default: data/submissions)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help='Number of concurrent download threads for bulk mode (default: 10)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay in seconds between downloads (default: 2.0)'
    )
    
    parser.add_argument(
        '--retry-attempts',
        type=int,
        default=3,
        help='Number of retry attempts for failed downloads (default: 3)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.cik:
            # Single CIK download
            downloader = SECSubmissionsDownloader(args.output_dir)
            file_path = downloader.download_and_save(args.cik)
            print(f"\nData saved to: {file_path}")
            
        elif args.bulk:
            # Bulk download
            downloader = SECSubmissionsDownloader(
                output_dir=args.output_dir,
                max_workers=args.workers,
                retry_attempts=args.retry_attempts,
                delay_seconds=args.delay
            )
            
            print(f"Starting bulk download with {args.workers} workers...")
            print(f"Delay between downloads: {args.delay} seconds")
            print(f"Retry attempts: {args.retry_attempts}")
            print(f"Output directory: {args.output_dir}")
            
            results = downloader.download_bulk_with_retry(args.bulk)
            
            # Save results summary
            today = datetime.now().strftime('%Y%m%d')
            date_dir = Path(args.output_dir) / today
            results_file = date_dir / "download_results.json"
            results_data = {
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
                "total_ciks": len(results),
                "successful": sum(1 for r in results if r.success),
                "failed": sum(1 for r in results if not r.success),
                "settings": {
                    "workers": args.workers,
                    "delay_seconds": args.delay,
                    "retry_attempts": args.retry_attempts
                },
                "results": [{
                    "cik": r.cik,
                    "success": r.success,
                    "company_name": r.company_name,
                    "file_path": r.file_path,
                    "error_message": r.error_message,
                    "attempt_count": r.attempt_count
                } for r in results]
            }
            
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            print(f"\nDownload results saved to: {results_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())