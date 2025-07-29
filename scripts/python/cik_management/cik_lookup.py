#!/usr/bin/env python3
"""
CIK Lookup Utility

This script provides utilities to search and lookup company information
from the downloaded CIK database.

Usage:
    python cik_lookup.py --ticker AAPL
    python cik_lookup.py --cik 0000320193
    python cik_lookup.py --name "Apple Inc"
    python cik_lookup.py --search apple
    python cik_lookup.py --stats
"""

import json
import csv
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional
import re

class CIKLookup:
    def __init__(self, data_dir="../../../data/cik_database"):
        """
        Initialize the CIK lookup utility.
        
        Args:
            data_dir (str): Directory containing the CIK database files
        """
        self.data_dir = Path(__file__).parent / data_dir
        self.companies = []
        self.load_data()
    
    def load_data(self):
        """
        Load the CIK database from JSON file.
        """
        json_file = self.data_dir / "cik_database.json"
        
        if not json_file.exists():
            print(f"Error: CIK database not found at {json_file}")
            print("Please run the download script first: download_cik_data.py")
            sys.exit(1)
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.companies = data.get('companies', [])
                self.metadata = data.get('metadata', {})
        except Exception as e:
            print(f"Error loading CIK database: {e}")
            sys.exit(1)
    
    def lookup_by_ticker(self, ticker: str) -> Optional[Dict]:
        """
        Find company by ticker symbol.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            dict: Company information or None if not found
        """
        ticker = ticker.upper().strip()
        for company in self.companies:
            if company.get('ticker', '').upper() == ticker:
                return company
        return None
    
    def lookup_by_cik(self, cik: str) -> Optional[Dict]:
        """
        Find company by CIK number.
        
        Args:
            cik (str): CIK number (can be padded or unpadded)
            
        Returns:
            dict: Company information or None if not found
        """
        # Normalize CIK (remove leading zeros for comparison)
        cik_normalized = str(int(cik)) if cik.isdigit() else cik
        
        for company in self.companies:
            company_cik = str(int(company.get('cik_raw', 0))) if str(company.get('cik_raw', '')).isdigit() else ''
            if company_cik == cik_normalized:
                return company
        return None
    
    def search_by_name(self, name: str, exact_match: bool = False) -> List[Dict]:
        """
        Search companies by name.
        
        Args:
            name (str): Company name or partial name
            exact_match (bool): Whether to perform exact match
            
        Returns:
            list: List of matching companies
        """
        name = name.lower().strip()
        matches = []
        
        for company in self.companies:
            company_name = company.get('company_name', '').lower()
            
            if exact_match:
                if company_name == name:
                    matches.append(company)
            else:
                if name in company_name:
                    matches.append(company)
        
        return matches
    
    def fuzzy_search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Perform fuzzy search across ticker and company name.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            
        Returns:
            list: List of matching companies
        """
        query = query.lower().strip()
        matches = []
        
        for company in self.companies:
            ticker = company.get('ticker', '').lower()
            name = company.get('company_name', '').lower()
            
            # Score based on relevance
            score = 0
            
            # Exact ticker match gets highest score
            if ticker == query:
                score = 100
            elif query in ticker:
                score = 80
            
            # Name matches
            if query in name:
                # Boost score if query is at the beginning of name
                if name.startswith(query):
                    score = max(score, 70)
                else:
                    score = max(score, 50)
            
            # Word boundary matches in name
            words = name.split()
            for word in words:
                if word.startswith(query):
                    score = max(score, 60)
                elif query in word:
                    score = max(score, 40)
            
            if score > 0:
                company_with_score = company.copy()
                company_with_score['_search_score'] = score
                matches.append(company_with_score)
        
        # Sort by score (descending) and limit results
        matches.sort(key=lambda x: x['_search_score'], reverse=True)
        return matches[:limit]
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the CIK database.
        
        Returns:
            dict: Database statistics
        """
        total_companies = len(self.companies)
        companies_with_tickers = len([c for c in self.companies if c.get('ticker')])
        companies_without_tickers = total_companies - companies_with_tickers
        
        # Get some sample tickers
        sample_tickers = [c['ticker'] for c in self.companies if c.get('ticker')][:10]
        
        return {
            'total_companies': total_companies,
            'companies_with_tickers': companies_with_tickers,
            'companies_without_tickers': companies_without_tickers,
            'last_updated': self.metadata.get('last_updated', 'Unknown'),
            'sample_tickers': sample_tickers
        }
    
    def format_company_info(self, company: Dict) -> str:
        """
        Format company information for display.
        
        Args:
            company (dict): Company information
            
        Returns:
            str: Formatted company information
        """
        ticker = company.get('ticker', 'N/A')
        name = company.get('company_name', 'N/A')
        cik = company.get('cik', 'N/A')
        cik_raw = company.get('cik_raw', 'N/A')
        
        return f"""
Ticker: {ticker}
Company Name: {name}
CIK (Padded): {cik}
CIK (Raw): {cik_raw}
"""

def main():
    parser = argparse.ArgumentParser(
        description="Lookup company information from CIK database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --ticker AAPL
  %(prog)s --cik 0000320193
  %(prog)s --name "Apple Inc"
  %(prog)s --search apple
  %(prog)s --stats
"""
    )
    
    parser.add_argument('--ticker', '-t', help='Lookup by ticker symbol')
    parser.add_argument('--cik', '-c', help='Lookup by CIK number')
    parser.add_argument('--name', '-n', help='Search by company name (exact match)')
    parser.add_argument('--search', '-s', help='Fuzzy search by ticker or name')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Limit search results (default: 10)')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    
    args = parser.parse_args()
    
    # Check if no arguments provided
    if not any([args.ticker, args.cik, args.name, args.search, args.stats]):
        parser.print_help()
        sys.exit(1)
    
    lookup = CIKLookup()
    
    if args.stats:
        stats = lookup.get_statistics()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print("CIK Database Statistics:")
            print("=" * 25)
            print(f"Total Companies: {stats['total_companies']:,}")
            print(f"Companies with Tickers: {stats['companies_with_tickers']:,}")
            print(f"Companies without Tickers: {stats['companies_without_tickers']:,}")
            print(f"Last Updated: {stats['last_updated']}")
            print(f"Sample Tickers: {', '.join(stats['sample_tickers'])}")
        return
    
    results = []
    
    if args.ticker:
        result = lookup.lookup_by_ticker(args.ticker)
        if result:
            results = [result]
    
    elif args.cik:
        result = lookup.lookup_by_cik(args.cik)
        if result:
            results = [result]
    
    elif args.name:
        results = lookup.search_by_name(args.name, exact_match=True)
    
    elif args.search:
        results = lookup.fuzzy_search(args.search, limit=args.limit)
    
    # Output results
    if args.json:
        # Remove search scores from JSON output
        clean_results = []
        for result in results:
            clean_result = {k: v for k, v in result.items() if not k.startswith('_')}
            clean_results.append(clean_result)
        print(json.dumps(clean_results, indent=2))
    else:
        if not results:
            print("No companies found matching your criteria.")
        else:
            print(f"Found {len(results)} result(s):\n")
            for i, company in enumerate(results, 1):
                print(f"Result {i}:")
                print("-" * 10)
                print(lookup.format_company_info(company))
                if i < len(results):
                    print()

if __name__ == "__main__":
    main()