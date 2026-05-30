# AI Company Enrichment Tool

## Features
- Scrapes company websites
- Extracts emails and phone numbers
- Uses Gemini AI to generate business insights
- Returns structured JSON output
- Stores results for analytics

## APIs

### POST /enrich
Input:
{
  "website_name": "IBM",
  "url": "https://www.ibm.com"
}

Output:
Structured company profile JSON

### GET /results
Returns all processed companies

## How to Run

pip install -r requirements.txt
python -m uvicorn app:app --reload