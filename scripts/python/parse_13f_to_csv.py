#!/usr/bin/env python3
"""
13F-HR SEC Filing Parser
Extracts holdings data from SEC 13F-HR text files and saves to CSV
"""

import os
import re
import csv
import pandas as pd
from datetime import datetime
from pathlib import Path
import argparse

class SEC13FParser:
    def __init__(self, output_csv="data/analysis/bridgewater_holdings.csv"):
        self.output_csv = output_csv
        self.holdings_data = []
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        
    def extract_filing_date(self, content):
        """
        Extract filing date from SEC document header
        """
        # Look for CONFORMED PERIOD OF REPORT or FILED AS OF DATE
        date_patterns = [
            r'CONFORMED PERIOD OF REPORT:\s*(\d{8})',
            r'FILED AS OF DATE:\s*(\d{8})',
            r'<ACCEPTANCE-DATETIME>(\d{8})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                date_str = match.group(1)
                try:
                    # Convert YYYYMMDD to datetime
                    return datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
                except:
                    continue
        
        return None
    
    def extract_accession_number(self, content):
        """
        Extract accession number from SEC document
        """
        match = re.search(r'ACCESSION NUMBER:\s*([0-9-]+)', content)
        return match.group(1) if match else None
    
    def parse_holdings_table(self, content):
        """
        Parse the holdings table from 13F-HR filing
        """
        holdings = []
        
        # Find the holdings table section
        # Look for table headers that indicate holdings data
        table_patterns = [
            r'NAME OF ISSUER.*?CLASS.*?CUSIP.*?VALUE.*?SHARES',
            r'NAME OF ISSUER.*?CUSIP.*?VALUE.*?SHARES',
            r'ISSUER.*?CUSIP.*?VALUE.*?SHARES'
        ]
        
        table_start = None
        for pattern in table_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                table_start = match.end()
                break
        
        if not table_start:
            return holdings
        
        # Extract table content after header
        table_content = content[table_start:]
        
        # Split into lines and process each potential holding entry
        lines = table_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 20:
                continue
                
            # Skip lines that look like headers or footers
            if any(keyword in line.upper() for keyword in 
                   ['TOTAL', 'SUBTOTAL', 'PAGE', 'CONTINUED', 'SIGNATURE', 'FORM 13F']):
                continue
            
            # Try to extract holding data using regex patterns
            # Pattern for: COMPANY NAME [CLASS] CUSIP VALUE SHARES [OTHER_DATA]
            holding_pattern = r'^([A-Z][A-Z\s&\.,\-\']+?)\s+([A-Z]*\s*)?([A-Z0-9]{8,9})\s+([0-9,]+)\s+([0-9,]+)'
            
            match = re.match(holding_pattern, line)
            if match:
                company_name = match.group(1).strip()
                share_class = match.group(2).strip() if match.group(2) else 'COM'
                cusip = match.group(3).strip()
                value = match.group(4).replace(',', '')
                shares = match.group(5).replace(',', '')
                
                # Validate extracted data
                if len(cusip) >= 8 and value.isdigit() and shares.isdigit():
                    holdings.append({
                        'company_name': company_name,
                        'share_class': share_class,
                        'cusip': cusip,
                        'value_thousands': int(value),
                        'shares': int(shares)
                    })
        
        return holdings
    
    def parse_file(self, file_path):
        """
        Parse a single 13F-HR file
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract metadata
            filing_date = self.extract_filing_date(content)
            accession_number = self.extract_accession_number(content)
            
            if not filing_date:
                print(f"⚠️  Could not extract filing date from {file_path}")
                return 0
            
            # Parse holdings
            holdings = self.parse_holdings_table(content)
            
            # Add metadata to each holding
            for holding in holdings:
                holding.update({
                    'filing_date': filing_date,
                    'accession_number': accession_number,
                    'source_file': os.path.basename(file_path)
                })
            
            self.holdings_data.extend(holdings)
            
            print(f"✅ Parsed {len(holdings)} holdings from {os.path.basename(file_path)} (Date: {filing_date})")
            return len(holdings)
            
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {str(e)}")
            return 0
    
    def save_to_csv(self):
        """
        Save all holdings data to CSV
        """
        if not self.holdings_data:
            print("❌ No holdings data to save")
            return
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(self.holdings_data)
        
        # Sort by filing date and company name
        df = df.sort_values(['filing_date', 'company_name'])
        
        # Reorder columns
        column_order = [
            'filing_date', 'accession_number', 'company_name', 'share_class',
            'cusip', 'value_thousands', 'shares', 'source_file'
        ]
        
        df = df[column_order]
        
        # Save to CSV
        df.to_csv(self.output_csv, index=False)
        
        print(f"\n📊 Holdings data saved to: {self.output_csv}")
        print(f"📈 Total holdings records: {len(df)}")
        print(f"📅 Date range: {df['filing_date'].min()} to {df['filing_date'].max()}")
        print(f"🏢 Unique companies: {df['company_name'].nunique()}")
        
        # Show sample data
        print("\n📋 Sample data:")
        print(df.head(10).to_string(index=False))

def main():
    parser = argparse.ArgumentParser(description='Parse 13F-HR SEC filings to CSV')
    parser.add_argument('--input-dir', default='data/sec_filings',
                       help='Directory containing SEC filing text files')
    parser.add_argument('--output-csv', default='data/analysis/bridgewater_holdings.csv',
                       help='Output CSV file path')
    parser.add_argument('--file-pattern', default='*.txt',
                       help='File pattern to match (default: *.txt)')
    
    args = parser.parse_args()
    
    # Initialize parser
    sec_parser = SEC13FParser(args.output_csv)
    
    # Find all text files
    input_path = Path(args.input_dir)
    if not input_path.exists():
        print(f"❌ Input directory does not exist: {args.input_dir}")
        return
    
    txt_files = list(input_path.glob(args.file_pattern))
    
    if not txt_files:
        print(f"❌ No files found matching pattern {args.file_pattern} in {args.input_dir}")
        return
    
    print(f"🚀 Starting to parse {len(txt_files)} files from {args.input_dir}")
    print(f"📁 Output will be saved to: {args.output_csv}")
    
    # Parse all files
    total_holdings = 0
    successful_files = 0
    
    for file_path in txt_files:
        holdings_count = sec_parser.parse_file(file_path)
        if holdings_count > 0:
            successful_files += 1
            total_holdings += holdings_count
    
    # Save results
    sec_parser.save_to_csv()
    
    print(f"\n🎯 Summary:")
    print(f"   📄 Files processed: {len(txt_files)}")
    print(f"   ✅ Successful: {successful_files}")
    print(f"   ❌ Failed: {len(txt_files) - successful_files}")
    print(f"   📊 Total holdings extracted: {total_holdings}")

if __name__ == "__main__":
    main()