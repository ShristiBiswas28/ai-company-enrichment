from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

import google.generativeai as genai

import requests
import json
import re
from bs4 import BeautifulSoup
import os
API_KEY = os.getenv("API_KEY")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

app = FastAPI()

all_results = []

@app.post("/enrich")
async def enrich(request: Request):

    body = await request.json()

    url = body.get("url")

    if not url:
        return {"error": "URL is required"}

    try:
        result = enrich_company(url)
        all_results.append(result)
        return result

    except Exception as e:
        return {
            "error": "Failed to process website",
            "details": str(e)
        }

def get_website_text(url):

    pages = [
        "",
        "/about",
        "/about-us",
        "/contact",
        "/contact-us",
        "/services"
    ]

    all_text = ""

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for page in pages:

        try:

            full_url = url.rstrip("/") + page

            response = requests.get(
                full_url,
                headers=headers,
                timeout=5
            )

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            for tag in soup(
                ["script", "style"]
            ):
                tag.decompose()

            text = soup.get_text(
                separator=" ",
                strip=True
            )

            all_text += "\n" + text

        except:
            pass

    return all_text[:20000]

def extract_emails(text, url):

    emails = re.findall(
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        text
    )

    domain = url.replace(
        "https://",
        ""
    )

    domain = domain.replace(
        "http://",
        ""
    )

    domain = domain.replace(
        "www.",
        ""
    )

    domain = domain.split("/")[0]

    filtered = []

    for email in emails:

        if domain.split(".")[0].lower() in email.lower():

            filtered.append(email)

    return list(set(filtered))

def extract_phone_numbers(text):

    phones = re.findall(
        r'\+?\d[\d\-\s\(\)]{7,}\d',
        text
    )

    return list(set(phones))

def get_company_insights(text):

    prompt = f"""
You are a strict business analyst.

Return ONLY valid JSON (no markdown, no explanation).

If information is missing, use "N/A".

Format:
{{
  "company_name": "N/A",
  "core_service": "N/A",
  "target_customer": "N/A",
  "probable_pain_point": "N/A",
  "outreach_opener": "N/A"
}}

Website text:
{text[:4000]}
"""

    response = model.generate_content(prompt)

    return response.text.strip()

def parse_ai_response(response_text):

    try:
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)

    except Exception:
        return {
            "company_name": "N/A",
            "core_service": "N/A",
            "target_customer": "N/A",
            "probable_pain_point": "N/A",
            "outreach_opener": "N/A"
        }
    
def enrich_company(url: str):

    text = get_website_text(url)

    emails = extract_emails(text, url)

    phones = extract_phone_numbers(text)

    ai_result = get_company_insights(text)

    ai_data = parse_ai_response(ai_result)

    result = {
        "website_name": url.split("//")[-1].replace("www.", ""),
        "company_name": ai_data.get("company_name", "N/A"),
        "address": "N/A",
        "mobile_number": phones[0] if phones else "N/A",
        "mail": emails,
        "core_service": ai_data.get("core_service", "N/A"),
        "target_customer": ai_data.get("target_customer", "N/A"),
        "probable_pain_point": ai_data.get("probable_pain_point", "N/A"),
        "outreach_opener": ai_data.get("outreach_opener", "N/A")
    }

    return result

@app.get("/", response_class=HTMLResponse)
def home():

    return """
<!DOCTYPE html>
<html>

<head>
<title>AI Company Enrichment</title>
</head>

<body>

<h1>AI Company Enrichment Tool</h1>

<label>Website Name</label>
<br>
<input type="text" id="website_name">
<br><br>

<label>Website URL</label>
<br>
<input type="text" id="website_url">
<br><br>

<button onclick="enrichCompany()">
Enrich
</button>

<hr>

<pre id="result" style="
background:#0d1117;
color:#00ff88;
padding:15px;
border-radius:10px;
overflow:auto;
">
No results yet.
</pre>

<script>

async function enrichCompany() {

    let websiteName =
        document.getElementById("website_name").value;

    let websiteUrl =
        document.getElementById("website_url").value;

    document.getElementById("result").innerText =
        "Loading...";

    let response =
        await fetch("/enrich", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                website_name: websiteName,
                url: websiteUrl
            })
        });

    let data = await response.json();

    document.getElementById("result").innerText =
        JSON.stringify(data, null, 2);
}

</script>

</body>
</html>
"""

@app.post("/enrich")
async def enrich(request: Request):

    body = await request.json()

    url = body.get("url")

    if not url:
        return {"error": "URL is required"}

    try:
        result = enrich_company(url)

        if not isinstance(result, dict):
            return {"error": "Invalid output from pipeline"}
        
        all_results.append(result)
        return result

    except Exception as e:
        return {
            "error": "Failed to process website",
            "details": str(e)
        }


@app.get("/test-ai")
def test_ai():

    response = model.generate_content(
        "Say hello in one sentence."
    )

    return {
        "response": response.text
    }

@app.get("/test-enrich")
def test_enrich():

    return enrich_company("https://www.ibm.com")

@app.get("/results")
def get_results():

    return {
        "count": len(all_results),
        "data": all_results
    }