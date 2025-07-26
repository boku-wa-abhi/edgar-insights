#!/usr/bin/env python3
"""
SEC Filing Timeline Analyzer using DeepSeek API
Analyzes SEC filings to create intelligent timelines and insights.
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

class DeepSeekTimelineAnalyzer:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # DeepSeek API configuration
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
        # Set up directories
        self.base_dir = Path(__file__).parent.parent.parent
        self.raw_data_dir = self.base_dir / 'data' / 'raw'
        self.analysis_dir = self.base_dir / 'data' / 'analysis'
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🤖 DeepSeek Timeline Analyzer initialized")
        print(f"📁 Raw data directory: {self.raw_data_dir}")
        print(f"📊 Analysis directory: {self.analysis_dir}")
    
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
    
    def load_filings_for_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """Load all SEC filings for a specific ticker"""
        ticker_dir = self.raw_data_dir / ticker
        if not ticker_dir.exists():
            print(f"❌ No data found for {ticker}")
            return []
        
        filings = []
        json_files = [f for f in ticker_dir.glob('*.json') if f.name != 'timeline_summary.json']
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    filing_data = json.load(f)
                filings.append(filing_data)
            except Exception as e:
                print(f"⚠️  Error reading {json_file.name}: {e}")
        
        # Sort by filing date
        filings.sort(key=lambda x: x.get('filing_date', ''), reverse=True)
        print(f"📄 Loaded {len(filings)} filings for {ticker}")
        return filings
    
    def call_deepseek_api(self, prompt: str, max_tokens: int = 2000) -> str:
        """Make API call to DeepSeek"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a financial analyst expert in SEC filings analysis. Provide detailed, accurate, and insightful analysis of SEC filings to create comprehensive timelines and identify key business events, financial trends, and strategic decisions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "stream": False
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            return f"Error: API request failed - {e}"
        except KeyError as e:
            print(f"❌ Unexpected API response format: {e}")
            return f"Error: Unexpected API response format - {e}"
    
    def create_filing_summary(self, filing: Dict[str, Any]) -> str:
        """Create a summary of a single filing using DeepSeek API"""
        content = filing.get('content', '')[:3000]  # Limit content for API
        form_type = filing.get('form', 'Unknown')
        filing_date = filing.get('filing_date', 'Unknown')
        
        prompt = f"""
Analyze this SEC filing and provide a concise summary:

Form Type: {form_type}
Filing Date: {filing_date}
Content Preview: {content}

Please provide:
1. Key business events or announcements
2. Financial highlights or concerns
3. Strategic decisions or changes
4. Regulatory or compliance matters
5. Impact on investors or stakeholders

Keep the summary concise but informative (max 200 words).
"""
        
        return self.call_deepseek_api(prompt, max_tokens=300)
    
    def create_comprehensive_timeline(self, ticker: str, filings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a comprehensive timeline analysis using DeepSeek API"""
        # Prepare filing summaries for context
        filing_summaries = []
        for filing in filings[:10]:  # Limit to most recent 10 filings
            summary = {
                'form': filing.get('form', 'Unknown'),
                'date': filing.get('filing_date', 'Unknown'),
                'content_preview': filing.get('content', '')[:500]
            }
            filing_summaries.append(summary)
        
        prompt = f"""
Analyze the following SEC filings for {ticker} and create a comprehensive business timeline:

Filings Data:
{json.dumps(filing_summaries, indent=2)}

Please provide a detailed analysis in JSON format with the following structure:
{{
  "company_overview": "Brief overview of the company and its business",
  "timeline_events": [
    {{
      "date": "YYYY-MM-DD",
      "event_type": "earnings|strategic|regulatory|operational|financial",
      "title": "Brief event title",
      "description": "Detailed description of what happened",
      "impact": "high|medium|low",
      "investor_significance": "Why this matters to investors"
    }}
  ],
  "key_trends": [
    "Trend 1: Description",
    "Trend 2: Description"
  ],
  "financial_highlights": [
    "Financial insight 1",
    "Financial insight 2"
  ],
  "risk_factors": [
    "Risk factor 1",
    "Risk factor 2"
  ],
  "strategic_direction": "Analysis of company's strategic direction",
  "investment_thesis": "Key points for investment consideration"
}}

Ensure the JSON is valid and comprehensive.
"""
        
        response = self.call_deepseek_api(prompt, max_tokens=3000)
        
        # Try to parse JSON response
        try:
            # Extract JSON from response if it's wrapped in markdown
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            elif '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
            else:
                json_str = response
            
            timeline_data = json.loads(json_str)
            return timeline_data
            
        except json.JSONDecodeError as e:
            print(f"⚠️  Could not parse JSON response for {ticker}: {e}")
            # Return a fallback structure
            return {
                "company_overview": f"Analysis for {ticker}",
                "timeline_events": [],
                "key_trends": ["Unable to parse detailed analysis"],
                "financial_highlights": [],
                "risk_factors": [],
                "strategic_direction": response[:500] + "...",
                "investment_thesis": "Please review raw analysis output",
                "raw_response": response
            }
    
    def analyze_ticker(self, ticker: str) -> bool:
        """Analyze all filings for a specific ticker"""
        print(f"\n🔍 Analyzing {ticker}...")
        
        # Load filings
        filings = self.load_filings_for_ticker(ticker)
        if not filings:
            print(f"⚠️  No filings found for {ticker}")
            return False
        
        # Create individual filing summaries
        print(f"📝 Creating filing summaries...")
        enhanced_filings = []
        for i, filing in enumerate(filings[:5]):  # Limit to 5 most recent for detailed analysis
            print(f"  Processing filing {i+1}/5: {filing.get('form', 'Unknown')}")
            summary = self.create_filing_summary(filing)
            
            enhanced_filing = filing.copy()
            enhanced_filing['ai_summary'] = summary
            enhanced_filings.append(enhanced_filing)
            
            # Rate limiting
            time.sleep(2)
        
        # Create comprehensive timeline
        print(f"🕒 Creating comprehensive timeline...")
        timeline_analysis = self.create_comprehensive_timeline(ticker, filings)
        
        # Combine all analysis
        complete_analysis = {
            "ticker": ticker,
            "analysis_date": datetime.now().isoformat(),
            "total_filings_analyzed": len(filings),
            "detailed_filings": enhanced_filings,
            "comprehensive_analysis": timeline_analysis,
            "metadata": {
                "analyzer": "DeepSeek Timeline Analyzer",
                "api_model": "deepseek-chat",
                "analysis_version": "1.0"
            }
        }
        
        # Save analysis
        analysis_file = self.analysis_dir / f"{ticker}_timeline_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(complete_analysis, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Analysis completed for {ticker}")
        print(f"📊 Saved to: {analysis_file}")
        return True
    
    def create_summary_report(self, analyzed_tickers: List[str]):
        """Create a summary report of all analyzed tickers"""
        print(f"\n📋 Creating summary report...")
        
        summary_data = {
            "report_date": datetime.now().isoformat(),
            "analyzed_tickers": analyzed_tickers,
            "total_companies": len(analyzed_tickers),
            "analysis_files": [f"{ticker}_timeline_analysis.json" for ticker in analyzed_tickers],
            "summary": f"Timeline analysis completed for {len(analyzed_tickers)} companies using DeepSeek AI"
        }
        
        summary_file = self.analysis_dir / "analysis_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Summary report saved to: {summary_file}")
    
    def run(self):
        """Main execution method"""
        print("🚀 Starting SEC filing timeline analysis...\n")
        
        # Load tickers
        tickers = self.load_tickers()
        if not tickers:
            print("❌ No tickers to analyze")
            return
        
        # Analyze each ticker
        successful_analyses = []
        for ticker in tickers:
            try:
                if self.analyze_ticker(ticker):
                    successful_analyses.append(ticker)
                    print(f"✅ {ticker} analysis completed")
                else:
                    print(f"⚠️  {ticker} analysis skipped")
            except Exception as e:
                print(f"❌ Error analyzing {ticker}: {e}")
            
            # Rate limiting between tickers
            if ticker != tickers[-1]:  # Don't sleep after last ticker
                print("⏳ Waiting 5 seconds before next ticker...")
                time.sleep(5)
        
        # Create summary report
        if successful_analyses:
            self.create_summary_report(successful_analyses)
        
        print("\n" + "="*60)
        print(f"🎉 Timeline analysis completed!")
        print(f"📊 Successfully analyzed: {len(successful_analyses)}/{len(tickers)} tickers")
        print(f"📁 Analysis files saved in: {self.analysis_dir}")
        print("\n📋 Generated files:")
        for ticker in successful_analyses:
            print(f"  • {ticker}_timeline_analysis.json")
        if successful_analyses:
            print(f"  • analysis_summary.json")
        print("\n💡 Use these analysis files to gain insights into company timelines and trends!")

if __name__ == "__main__":
    analyzer = DeepSeekTimelineAnalyzer()
    analyzer.run()