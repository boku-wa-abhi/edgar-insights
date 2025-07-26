from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
import json
from typing import List
import markdown
from xhtml2pdf import pisa  # For PDF generation

app = FastAPI()

DATA_DIR = '../data'

@app.get("/filings/{ticker}")
def get_filings(ticker: str):
    ticker_dir = os.path.join(DATA_DIR, ticker)
    if not os.path.exists(ticker_dir):
        raise HTTPException(status_code=404, detail="No filings found for this ticker")
    
    filings = []
    for filing_folder in os.listdir(ticker_dir):
        folder_path = os.path.join(ticker_dir, filing_folder)
        if os.path.isdir(folder_path):
            try:
                with open(os.path.join(folder_path, 'filing.json'), 'r') as f:
                    metadata = json.load(f)
                with open(os.path.join(folder_path, 'summary.json'), 'r') as f:
                    summary = json.load(f)
                filings.append({
                    'date': metadata.get('date'),
                    'type': metadata.get('type'),
                    'summary': summary.get('summary')
                })
            except Exception as e:
                continue
    
    filings.sort(key=lambda x: x['date'], reverse=True)  # Sort by date descending
    return filings

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