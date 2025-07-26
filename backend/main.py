from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
import json
from typing import List
import markdown
from xhtml2pdf import pisa  # For PDF generation
from pathlib import Path

app = FastAPI()

DATA_DIR = '../data/raw'  # Use raw data for the application

@app.get("/filings/{ticker}")
async def get_filings(ticker: str):
    """Get SEC filings for a specific ticker"""
    ticker_dir = Path(DATA_DIR) / ticker.upper()
    
    if not ticker_dir.exists():
        raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")
    
    # Check for timeline_summary.json first
    timeline_file = ticker_dir / "timeline_summary.json"
    
    if timeline_file.exists():
        try:
            with open(timeline_file, 'r') as f:
                timeline_data = json.load(f)
            
            # Extract filings metadata and create filing objects
            filings = []
            for filing_meta in timeline_data.get("filings_metadata", []):
                filing_data = {
                    "ticker": ticker.upper(),
                    "form": filing_meta.get("form", "Unknown"),
                    "date": filing_meta.get("date", ""),
                    "type": filing_meta.get("form", "Unknown"),
                    "accession_number": filing_meta.get("accession", ""),
                    "company_name": timeline_data.get("ticker", ticker.upper()),
                    "filing_url": "",
                    "summary": timeline_data.get("ai_timeline", timeline_data.get("summary", "No summary available"))
                }
                filings.append(filing_data)
            
            # Sort by date (newest first)
            filings.sort(key=lambda x: x.get("date", ""), reverse=True)
            
            return {
                "ticker": ticker.upper(), 
                "filings": filings,
                "timeline": timeline_data.get("ai_timeline", timeline_data.get("basic_timeline", [])),
                "summary": timeline_data.get("summary", "No summary available"),
                "generated_at": timeline_data.get("generated_at", "")
            }
            
        except json.JSONDecodeError:
            pass
    
    # Fallback to old structure if timeline_summary.json doesn't exist
    filings = []
    
    # Iterate through filing directories (old structure)
    for filing_dir in ticker_dir.iterdir():
        if filing_dir.is_dir():
            filing_json = filing_dir / "filing.json"
            summary_json = filing_dir / "summary.json"
            
            if filing_json.exists():
                try:
                    # Load filing metadata
                    with open(filing_json, 'r') as f:
                        filing_data = json.load(f)
                    
                    # Load summary if available
                    if summary_json.exists():
                        with open(summary_json, 'r') as f:
                            summary_data = json.load(f)
                        filing_data["summary"] = summary_data.get("summary", "No summary available")
                    else:
                        filing_data["summary"] = "No summary available"
                    
                    filings.append(filing_data)
                    
                except json.JSONDecodeError:
                    continue
    
    # Sort by date (newest first)
    filings.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    return {"ticker": ticker.upper(), "filings": filings}

@app.get("/download/{ticker}")
def download_report(ticker: str, format: str = 'markdown'):
    filings = get_filings(ticker)  # Reuse the function
    if not filings:
        raise HTTPException(status_code=404, detail="No filings to download")
    
    content = f"# SEC Filings Timeline for {ticker}\n\n"
    for filing in filings:
        content += f"## {filing['date']} - {filing['type']}\n\n{filing['summary']}\n\n"
    
    if format == 'markdown':
        file_path = f"/tmp/{ticker}_report.md"
        with open(file_path, 'w') as f:
            f.write(content)
        return FileResponse(file_path, media_type='text/markdown', filename=f"{ticker}_report.md")
    elif format == 'pdf':
        html = markdown.markdown(content)
        file_path = f"/tmp/{ticker}_report.pdf"
        with open(file_path, 'w+b') as f:
            pisa.CreatePDF(html, dest=f)
        return FileResponse(file_path, media_type='application/pdf', filename=f"{ticker}_report.pdf")
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'markdown' or 'pdf'")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)