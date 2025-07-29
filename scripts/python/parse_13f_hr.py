#!/usr/bin/env python3
"""
13F-HR Parser for Bridgewater Associates Filing
Parses 13F-HR XML data and extracts holdings information
"""

import xml.etree.ElementTree as ET
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

class ThirteenFParser:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.raw_data = None
        self.parsed_data = {
            'filing_info': {},
            'summary': {},
            'holdings': []
        }
    
    def load_file(self):
        """Load the 13F-HR text file"""
        try:
            print(f"🔍 Attempting to load file: {self.file_path}")
            print(f"📁 File exists: {self.file_path.exists()}")
            
            if not self.file_path.exists():
                print(f"❌ File not found: {self.file_path}")
                return False
            
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
            
            for encoding in encodings:
                try:
                    with open(self.file_path, 'r', encoding=encoding) as f:
                        self.raw_data = f.read()
                    
                    if self.raw_data:
                        print(f"✅ Loaded 13F-HR file with {encoding} encoding: {self.file_path}")
                        print(f"📊 File size: {len(self.raw_data):,} characters")
                        return True
                    else:
                        print(f"⚠️ File loaded with {encoding} but is empty")
                        
                except UnicodeDecodeError:
                    print(f"❌ Failed to decode with {encoding}")
                    continue
            
            print(f"❌ Could not load file with any encoding")
            return False
            
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return False
    
    def extract_xml_sections(self):
        """Extract XML sections from the raw data"""
        print("🔍 Extracting XML sections...")
        
        # Split documents and process each separately
        documents = re.split(r'</DOCUMENT>', self.raw_data)
        
        form_xml = None
        info_table_xml = None
        
        for doc in documents:
             if '<TYPE>13F-HR' in doc:
                 # Extract XML from 13F-HR document
                 xml_match = re.search(r'<XML>(.*?)</XML>', doc, re.DOTALL)
                 if xml_match:
                     form_xml = xml_match.group(1).strip()
                     print(f"Found 13F-HR XML: {len(form_xml)} characters")
             elif '<TYPE>INFORMATION TABLE' in doc:
                 # Extract XML from INFORMATION TABLE document
                 xml_match = re.search(r'<XML>(.*?)</XML>', doc, re.DOTALL)
                 if xml_match:
                     info_table_xml = xml_match.group(1).strip()
                     print(f"Found INFO TABLE XML: {len(info_table_xml)} characters")
        
        if form_xml and info_table_xml:
            print(f"✅ Successfully extracted XML sections")
            print(f"Form XML starts with: {form_xml[:100]}")
            print(f"Info XML starts with: {info_table_xml[:100]}")
            return form_xml, info_table_xml
        
        print("❌ Failed to extract XML sections")
        return None, None
    
    def parse_filing_info(self, form_xml: str):
        """Parse filing information from the main form XML"""
        try:
            # Clean up XML namespaces for easier parsing
            clean_xml = re.sub(r'xmlns[^=]*="[^"]*"', '', form_xml)
            clean_xml = re.sub(r'xsi:[^=]*="[^"]*"', '', clean_xml)
            clean_xml = re.sub(r'ns1:', '', clean_xml)
            
            root = ET.fromstring(clean_xml)
            
            # Extract filing information
            filing_info = {
                'filer_name': self._get_text(root, './/name'),
                'cik': self._get_text(root, './/cik'),
                'period_of_report': self._get_text(root, './/periodOfReport'),
                'report_type': self._get_text(root, './/reportType'),
                'form_13f_file_number': self._get_text(root, './/form13FFileNumber'),
                'address': {
                    'street': self._get_text(root, './/street1'),
                    'city': self._get_text(root, './/city'),
                    'state': self._get_text(root, './/stateOrCountry'),
                    'zip_code': self._get_text(root, './/zipCode')
                },
                'signature': {
                    'name': self._get_text(root, './/signatureBlock/name'),
                    'title': self._get_text(root, './/signatureBlock/title'),
                    'phone': self._get_text(root, './/signatureBlock/phone'),
                    'date': self._get_text(root, './/signatureDate')
                }
            }
            
            # Extract summary information
            summary = {
                'total_entries': int(self._get_text(root, './/tableEntryTotal') or 0),
                'total_value': int(self._get_text(root, './/tableValueTotal') or 0),
                'other_managers_count': int(self._get_text(root, './/otherIncludedManagersCount') or 0)
            }
            
            self.parsed_data['filing_info'] = filing_info
            self.parsed_data['summary'] = summary
            
            print(f"✅ Parsed filing info for {filing_info['filer_name']}")
            print(f"📊 Total holdings: {summary['total_entries']:,}")
            print(f"💰 Total value: ${summary['total_value']:,}")
            
        except Exception as e:
            print(f"❌ Error parsing filing info: {e}")
    
    def parse_holdings(self, info_table_xml: str):
        """Parse holdings information from the information table XML"""
        try:
            # Clean up XML namespaces more thoroughly
            clean_xml = re.sub(r'xmlns[^=]*="[^"]*"', '', info_table_xml)
            clean_xml = re.sub(r'xsi:[^=]*="[^"]*"', '', clean_xml)
            clean_xml = re.sub(r'n1:', '', clean_xml)
            clean_xml = re.sub(r'xsi:schemaLocation="[^"]*"', '', clean_xml)
            
            root = ET.fromstring(clean_xml)
            
            holdings = []
            
            for info_table in root.findall('.//infoTable'):
                holding = {
                    'issuer_name': self._get_text(info_table, 'nameOfIssuer'),
                    'title_of_class': self._get_text(info_table, 'titleOfClass'),
                    'cusip': self._get_text(info_table, 'cusip'),
                    'value': int(self._get_text(info_table, 'value') or 0),
                    'shares': int(self._get_text(info_table, './/sshPrnamt') or 0),
                    'share_type': self._get_text(info_table, './/sshPrnamtType'),
                    'investment_discretion': self._get_text(info_table, 'investmentDiscretion'),
                    'voting_authority': {
                        'sole': int(self._get_text(info_table, './/Sole') or 0),
                        'shared': int(self._get_text(info_table, './/Shared') or 0),
                        'none': int(self._get_text(info_table, './/None') or 0)
                    }
                }
                
                # Calculate price per share
                if holding['shares'] > 0:
                    holding['price_per_share'] = round(holding['value'] / holding['shares'], 2)
                else:
                    holding['price_per_share'] = 0
                
                holdings.append(holding)
            
            # Sort by value (descending)
            holdings.sort(key=lambda x: x['value'], reverse=True)
            
            self.parsed_data['holdings'] = holdings
            print(f"✅ Parsed {len(holdings)} holdings")
            
        except Exception as e:
            print(f"❌ Error parsing holdings: {e}")
    
    def _get_text(self, element, xpath: str) -> str:
        """Helper method to safely get text from XML element"""
        try:
            found = element.find(xpath)
            return found.text.strip() if found is not None and found.text else ''
        except:
            return ''
    
    def parse(self):
        """Main parsing method"""
        if not self.load_file():
            return False
        
        print("🔍 Extracting XML sections...")
        form_xml, info_table_xml = self.extract_xml_sections()
        
        if not form_xml or not info_table_xml:
            print("❌ Could not extract XML sections")
            return False
        
        print("📋 Parsing filing information...")
        self.parse_filing_info(form_xml)
        
        print("📊 Parsing holdings data...")
        self.parse_holdings(info_table_xml)
        
        return True
    
    def save_json(self, output_path: str = None):
        """Save parsed data to JSON file"""
        if not output_path:
            output_path = self.file_path.parent / f"{self.file_path.stem}_parsed.json"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.parsed_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved parsed data to: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")
            return None
    
    def get_top_holdings(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N holdings by value"""
        return self.parsed_data['holdings'][:n]
    
    def get_holdings_by_sector(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group holdings by sector (simplified categorization)"""
        # This is a simplified categorization - in a real app, you'd use a proper sector mapping
        sectors = {
            'Technology': [],
            'Healthcare': [],
            'Financial': [],
            'Consumer': [],
            'Industrial': [],
            'Energy': [],
            'Other': []
        }
        
        tech_keywords = ['TECH', 'SOFTWARE', 'MICROSOFT', 'APPLE', 'GOOGLE', 'META', 'AMAZON', 'NVIDIA']
        health_keywords = ['HEALTH', 'PHARMA', 'MEDICAL', 'BIO', 'JOHNSON', 'PFIZER']
        financial_keywords = ['BANK', 'FINANCIAL', 'INSURANCE', 'CAPITAL', 'JPMORGAN', 'GOLDMAN']
        
        for holding in self.parsed_data['holdings']:
            name = holding['issuer_name'].upper()
            
            if any(keyword in name for keyword in tech_keywords):
                sectors['Technology'].append(holding)
            elif any(keyword in name for keyword in health_keywords):
                sectors['Healthcare'].append(holding)
            elif any(keyword in name for keyword in financial_keywords):
                sectors['Financial'].append(holding)
            elif 'CONSUMER' in name or 'RETAIL' in name:
                sectors['Consumer'].append(holding)
            elif 'ENERGY' in name or 'OIL' in name:
                sectors['Energy'].append(holding)
            elif 'INDUSTRIAL' in name:
                sectors['Industrial'].append(holding)
            else:
                sectors['Other'].append(holding)
        
        return sectors
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate portfolio statistics"""
        holdings = self.parsed_data['holdings']
        total_value = sum(h['value'] for h in holdings)
        
        if not holdings:
            return {}
        
        values = [h['value'] for h in holdings]
        
        stats = {
            'total_holdings': len(holdings),
            'total_value': total_value,
            'average_position_size': total_value / len(holdings),
            'largest_position': max(values),
            'smallest_position': min(values),
            'top_10_concentration': sum(h['value'] for h in holdings[:10]) / total_value * 100,
            'median_position_size': sorted(values)[len(values) // 2]
        }
        
        return stats

def main():
    """Main function for testing"""
    # Use relative path from the script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    file_path = project_root / '13F-HR.txt'
    
    parser = ThirteenFParser(file_path)
    
    if parser.parse():
        # Save parsed data
        output_path = project_root / 'data' / 'analysis' / 'bridgewater_13f_parsed.json'
        output_file = parser.save_json(output_path)
        
        # Print some statistics
        stats = parser.get_statistics()
        print("\n📈 Portfolio Statistics:")
        for key, value in stats.items():
            if 'value' in key or 'size' in key or 'position' in key:
                print(f"  {key.replace('_', ' ').title()}: ${value:,.0f}")
            elif 'concentration' in key:
                print(f"  {key.replace('_', ' ').title()}: {value:.1f}%")
            else:
                print(f"  {key.replace('_', ' ').title()}: {value:,}")
        
        # Show top 5 holdings
        print("\n🏆 Top 5 Holdings:")
        for i, holding in enumerate(parser.get_top_holdings(5), 1):
            print(f"  {i}. {holding['issuer_name']}: ${holding['value']:,} ({holding['shares']:,} shares)")

if __name__ == "__main__":
    main()