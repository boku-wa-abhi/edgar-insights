#!/usr/bin/env python3
"""
SEC EDGAR Archive Scraper for Bridgewater Associates

This script scrapes the SEC EDGAR archive for Bridgewater Associates (CIK: 1350694)
and downloads all .txt files from each filing folder.

Usage:
    python sec_scraper.py
"""

import requests
import os
import re
import time
from urllib.parse import urljoin, urlparse
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Set

class SECScraper:
    def __init__(self, base_url: str, download_dir: str = "data/sec_filings"):
        """
        Initialize the SEC scraper
        
        Args:
            base_url: Base URL for the SEC archive
            download_dir: Directory to save downloaded files
        """
        self.base_url = base_url.rstrip('/')
        self.download_dir = Path(download_dir)
        self.session = requests.Session()
        
        # Set headers that comply with SEC requirements
        # SEC requires a proper User-Agent that identifies the requester
        self.session.headers.update({
            'User-Agent': 'Edgar Insights Scraper (contact: user@example.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Host': 'www.sec.gov',
        })
        
        # Create download directory
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting - SEC recommends being respectful with request frequency
        self.request_delay = 2.0  # Delay between requests in seconds
        
    def get_page_content(self, url: str) -> BeautifulSoup:
        """
        Fetch and parse a web page
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object of the parsed HTML
        """
        try:
            print(f"📡 Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Rate limiting
            time.sleep(self.request_delay)
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.RequestException as e:
            print(f"❌ Error fetching {url}: {e}")
            return None
    
    def extract_folder_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract folder links from SEC directory listing
        Look for accession numbers in table rows since the directory listing uses tables
        
        Args:
            soup: BeautifulSoup object of the directory page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of folder URLs
        """
        folder_links = []
        
        print("\n🔍 Debug: Looking for accession numbers in table rows...")
        
        # Find all table rows
        table_rows = soup.find_all('tr')
        
        for row in table_rows:
            cells = row.find_all(['td', 'th'])
            if cells and len(cells) >= 1:
                # The first cell typically contains the accession number
                first_cell = cells[0].get_text(strip=True)
                
                # Check if this looks like an accession number
                # Can be format: XXXXXXXXXX-XX-XXXXXX or just 18 digits like 000117266125001828
                if (re.match(r'^\d{10}-\d{2}-\d{6}$', first_cell) or 
                    re.match(r'^\d{18}$', first_cell)):
                    print(f"  ✅ Found accession number: {first_cell}")
                    # Build the folder URL
                    folder_url = f"{base_url.rstrip('/')}/{first_cell}/"
                    folder_links.append(folder_url)
                else:
                    # Debug: show what we're checking
                    if first_cell and len(first_cell) > 5:  # Only show substantial content
                        print(f"  ❌ Not an accession number: '{first_cell}'")
        
        print(f"\n📁 Total folders found: {len(folder_links)}")
        return folder_links
    
    def find_txt_files(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Find .txt files in a folder
        
        Args:
            soup: BeautifulSoup object of the folder page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of .txt file URLs
        """
        txt_files = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if href.endswith('.txt'):
                full_url = urljoin(base_url, href)
                txt_files.append(full_url)
                print(f"📄 Found txt file: {href}")
        
        return txt_files
    
    def download_file(self, url: str, local_path: Path) -> bool:
        """
        Download a file from URL to local path
        
        Args:
            url: URL to download
            local_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"⬇️  Downloading: {url}")
            
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # Create parent directories if they don't exist
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Saved: {local_path}")
            
            # Rate limiting
            time.sleep(self.request_delay)
            
            return True
            
        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")
            return False
    
    def scrape_archive(self) -> None:
        """
        Main scraping method - discovers folders and downloads .txt files
        """
        print(f"🚀 Starting SEC archive scrape: {self.base_url}")
        print(f"📂 Download directory: {self.download_dir}")
        
        # Get the main archive page
        soup = self.get_page_content(self.base_url)
        if not soup:
            print("❌ Failed to fetch main archive page")
            return
        
        # Debug: Check page structure
        all_links = soup.find_all('a', href=True)
        print(f"🔍 Analyzing {len(all_links)} links on the page")
        
        # Show first 20 links to understand structure
        print("\n📋 First 20 links found:")
        for i, link in enumerate(all_links[:20]):
            href = link['href']
            text = link.get_text(strip=True)[:50]  # Limit text length
            print(f"  {i+1:2d}. href='{href}' text='{text}'")
        
        # Look for directory content in different ways
        print("\n🔍 Looking for directory content...")
        
        # Check for pre-formatted text (common in directory listings)
        pre_tags = soup.find_all('pre')
        if pre_tags:
            print(f"Found {len(pre_tags)} <pre> tags")
            for i, pre in enumerate(pre_tags):
                content = pre.get_text()[:200]
                print(f"  Pre {i+1}: {content}")
        
        # Check for table rows (another common format)
        table_rows = soup.find_all('tr')
        if table_rows:
            print(f"Found {len(table_rows)} table rows")
            for i, row in enumerate(table_rows[:10]):
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_text = ' | '.join([cell.get_text(strip=True) for cell in cells])
                    print(f"  Row {i+1}: {row_text}")
        
        # Look for any links that contain accession numbers
        accession_links = []
        for link in all_links:
            href = link['href']
            if re.search(r'\d{10}-\d{2}-\d{6}', href):
                accession_links.append(href)
        
        if accession_links:
            print(f"\n📁 Found {len(accession_links)} links with accession numbers:")
            for link in accession_links[:10]:
                print(f"  {link}")
        else:
            print("\n❌ No accession number patterns found in any links")
        
        # Extract folder links
        folder_links = self.extract_folder_links(soup, self.base_url)
        
        if not folder_links:
            print("❌ No folders found in archive")
            return
        
        print(f"📊 Found {len(folder_links)} folders to process")
        
        downloaded_count = 0
        failed_count = 0
        
        # Process each folder
        for i, folder_url in enumerate(folder_links, 1):
            print(f"\n📁 Processing folder {i}/{len(folder_links)}: {folder_url}")
            
            # Get folder content
            folder_soup = self.get_page_content(folder_url)
            if not folder_soup:
                failed_count += 1
                continue
            
            # Find .txt files in this folder
            txt_files = self.find_txt_files(folder_soup, folder_url)
            
            if not txt_files:
                print("   ⚠️  No .txt files found in this folder")
                continue
            
            # Download each .txt file
            for txt_url in txt_files:
                # Create local filename based on URL structure
                parsed_url = urlparse(txt_url)
                path_parts = parsed_url.path.strip('/').split('/')
                
                # Use the last few path components to create a meaningful filename
                if len(path_parts) >= 2:
                    folder_name = path_parts[-2]  # Parent folder name
                    file_name = path_parts[-1]    # File name
                    local_filename = f"{folder_name}_{file_name}"
                else:
                    local_filename = path_parts[-1]
                
                local_path = self.download_dir / local_filename
                
                # Skip if file already exists
                if local_path.exists():
                    print(f"   ⏭️  Skipping existing file: {local_filename}")
                    continue
                
                # Download the file
                if self.download_file(txt_url, local_path):
                    downloaded_count += 1
                else:
                    failed_count += 1
        
        # Summary
        print(f"\n📈 Scraping completed!")
        print(f"✅ Downloaded: {downloaded_count} files")
        print(f"❌ Failed: {failed_count} files")
        print(f"📂 Files saved to: {self.download_dir}")

def main():
    """
    Main function to run the scraper
    """
    # Bridgewater Associates CIK: 1350694
    # Try the direct archive URL again but with different approach
    base_url = "https://www.sec.gov/Archives/edgar/data/1350694/"
    
    print(f"🔍 Testing direct access to: {base_url}")
    
    # Initialize scraper
    scraper = SECScraper(base_url)
    
    # Test the page first
    soup = scraper.get_page_content(base_url)
    if soup:
        # Check if we're getting redirected by looking at the page title
        title = soup.find('title')
        if title:
            print(f"📄 Page title: {title.get_text()}")
        
        # Look for any text that might indicate this is a directory listing
        page_text = soup.get_text()[:500]
        print(f"📝 Page content preview: {page_text[:200]}...")
        
        # Check if this looks like a directory listing
        if "Index of" in page_text or "Directory" in page_text:
            print("✅ Looks like a directory listing")
            scraper.scrape_archive()
        else:
            print("❌ This doesn't appear to be a directory listing")
            print("💡 The SEC might be blocking direct archive access")
    else:
        print("❌ Failed to access the URL")

if __name__ == "__main__":
    main()