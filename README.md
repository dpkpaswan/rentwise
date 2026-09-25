<div align="center">

# RentWise (ClauseCheck)

**AI-Powered Rental Agreement Risk Checker for Tenants in India**

[![Tests](https://img.shields.io/badge/tests-16%20passed-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)]()
[![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB.svg)]()
[![Google Gemini](https://img.shields.io/badge/AI-Gemini%203.8%20Flash-4285F4.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

Understand your rental agreement before you sign.  
Upload your contract, get a plain-English breakdown, detect unfair clauses, and know what to ask a lawyer.

🌐 **Live Application:** [https://rentwise-juvt.onrender.com](https://rentwise-juvt.onrender.com)

---

> **⚠️ Disclaimer:** This tool provides general educational information only, not legal advice. Always consult a qualified lawyer before signing any rental agreement.

</div>

---

## The Problem

Millions of tenants in India sign rental agreements without fully understanding the terms. Legal language is dense, unfair clauses are easily missed, and hiring a lawyer to review every standard agreement is often expensive and inconvenient.

Common pitfalls include:
- Excessive security deposits (e.g. 10+ months without interest)
- Automatic rent escalation clauses with steep year-on-year increases
- Unrestricted landlord entry rights without notice
- One-sided lock-in periods and unfair deposit forfeiture terms
- Vague maintenance charges and arbitrary deduction rules

**RentWise bridges this gap.** It gives tenants a clear, jargon-free breakdown of their agreement, highlighting risks and generating targeted questions for legal counsel.

---

## Features

| Feature | Description |
|---|---|
| **📄 PDF & Text Ingestion** | Upload a PDF or paste agreement text directly. Text is parsed in-memory using `pypdf`. Clear errors for scanned/image-only PDFs. |
| **📝 5-Bullet Plain Summary** | Exactly 5 concise, jargon-free bullet points capturing the core terms (rent, deposit, duration, notice, obligations). |
| **🚩 Verified Red Flags** | Identifies risky clauses with severity ratings (`High`, `Medium`, `Low`), tenant risk explanations, and renegotiation suggestions. |
| **🔍 Quote Verification** | **Anti-hallucination engine:** Every quoted clause is verified verbatim against the source text. Unverified flags are discarded. |
| **💬 Grounded Follow-up Q&A** | Chat interface to ask questions about the agreement. Responses are strictly grounded in document text and cite exact clauses. |
| **⚖️ Lawyer Consultation List** | Generates tailored questions based on your specific contract to discuss with a qualified legal professional. |
| **📋 Built-in Sample Contract** | One-click demo with a pre-loaded Indian rental agreement featuring realistic common traps. |

---

## Architecture & Security

### System Overview

```
┌───────────────────────────┐
│     Client (Browser)      │
│  React (Vite) + Plain CSS │
└─────────────┬─────────────┘
              │ HTTPS / REST (JSON + Multipart)
              ▼
┌───────────────────────────┐
│      FastAPI Backend      │
│  • Memory-only processing │
│  • Rate / size limits     │
│  • Quote verification     │
└─────────────┬─────────────┘
              │ SSL / google-genai SDK
              ▼
┌───────────────────────────┐
│   Google Gemini API       │
│   (gemini-3.8-flash)      │
└───────────────────────────┘
```

### Security & Privacy Controls

1. **Zero Data Persistence**: No database, no user accounts, and no disk caching. Files are processed entirely in ephemeral RAM and discarded immediately.
2. **Streaming File Upload Limit (5 MB)**: Uploads are read in chunks up to 5 MB. Files exceeding 5 MB are aborted immediately with `HTTP 413 Payload Too Large`, preventing memory exhaustion / DoS attacks.
3. **Input Quota Protections**:
   - `/ask` question capped at **2,000 characters**.
   - Document text capped at **100,000 characters** (~50 pages of plain text).
   - Minimum text threshold (50 characters) prevents empty/useless API invocations.
4. **Sanitized Error Responses**: Internal tracebacks, file paths, and exception messages are logged strictly server-side and never exposed to the client.
5. **Restricted CORS**: Whitelisted origins for local development and production (`https://rentwise-juvt.onrender.com`), restricted to `GET`, `POST`, and `OPTIONS`.
6. **Credential Protection**: `GEMINI_API_KEY` is loaded exclusively from environment variables. Git history is audited and contains no credentials.

---

## API Reference

### `GET /health`
Health check endpoint.
- **Response:** `200 OK`
```json
{ "status": "ok" }
```

### `GET /sample`
Retrieves the built-in sample rental agreement for testing and demonstration.
- **Response:** `200 OK`
```json
{ "text": "RENTAL AGREEMENT\nThis Rental Agreement..." }
```

### `POST /analyze`
Analyzes a rental agreement supplied as a PDF file or pasted text form.
- **Parameters:**
  - `file`: `UploadFile` (optional, max 5 MB)
  - `text`: `string` (optional, 50 to 100,000 characters)
- **Response:** `200 OK`
```json
{
  "summary": ["Monthly rent is Rs. 25,000.", "..."],
  "red_flags": [
    {
      "clause_quote": "The tenant shall pay a security deposit of Rs. 2,50,000 equivalent to 10 months rent.",
      "risk": "10 months deposit is excessively high for Indian rental norms.",
      "severity": "High",
      "suggestion": "Request reducing security deposit to standard 2-3 months rent."
    }
  ],
  "flags": [ ... ],
  "lawyer_questions": ["Is the lock-in period legally enforceable?"],
  "document_text": "Full extracted text..."
}
```

### `POST /ask`
Answers follow-up questions grounded strictly in the provided document text.
- **Payload:**
```json
{
  "document_text": "Agreement text here...",
  "question": "What is the notice period for terminating the agreement?"
}
```
- **Response:** `200 OK`
```json
{
  "answer": "The agreement specifies a notice period of 1 month in writing.",
  "source_quote": "Either party may terminate by providing one month written notice."
}
```

---

## Local Development

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- A [Google Gemini API Key](https://aistudio.google.com/apikey)

### 1. Clone & Setup Backend

```bash
# Clone the repository
git clone https://github.com/dpkpaswan/rentwise.git
cd rentwise/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Set Gemini API key
export GEMINI_API_KEY=your_gemini_api_key_here     # macOS / Linux
$env:GEMINI_API_KEY="your_gemini_api_key_here"      # Windows PowerShell

# Start FastAPI server
uvicorn main:app --reload --port 8000
```

### 2. Setup Frontend

```bash
cd ../frontend
npm install
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) in your browser.

---

## Running Tests

RentWise includes a comprehensive automated test suite powered by `pytest` and `httpx`.

The suite covers:
- Endpoint health and status codes
- Input validation (empty text, whitespace, missing fields)
- Server-side file upload limits (5 MB rejection with HTTP 413)
- API character limits (2,000-char questions, 100k-char documents)
- Information leakage and traceback prevention
- Anti-hallucination clause quote verification logic

```bash
# From repository root:
pytest tests/

# Or with verbose output:
pytest tests/ -v

# Or from within the backend directory:
cd backend
pytest tests/ -v
```

---

## Deployment

### Deploy to Render (Docker Web Service)

1. Connect your GitHub repository to [Render](https://render.com).
2. Create a new **Web Service** using Docker.
3. Configure the following environment variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `PORT`: `8080` (or leave default)
4. Deploy! The multi-stage `Dockerfile` automatically builds the React SPA and serves it from FastAPI.

### Deploy to Google Cloud Run

```bash
# 1. Build and push image to Google Artifact Registry / GCR
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/rentwise

# 2. Deploy to Cloud Run
gcloud run deploy rentwise \
  --image gcr.io/YOUR_PROJECT_ID/rentwise \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-api-key-here
```

---

## Project Structure

```
rentwise/
├── backend/
│   ├── main.py                  # FastAPI application with endpoints & middleware
│   ├── models.py                # Pydantic data schemas with validation
│   ├── gemini_service.py        # Gemini API integration & quote verification
│   ├── sample_agreement.py      # Sample Indian rental agreement for testing
│   ├── requirements.txt         # Backend dependencies (fastapi, pypdf, pytest, etc.)
│   └── tests/
│       ├── __init__.py
│       ├── test_api.py          # API route & boundary test cases
│       └── test_verify_quotes.py# Anti-hallucination quote verification unit tests
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main React SPA component
│   │   ├── index.css            # Complete design system & responsive styling
│   │   └── main.jsx             # React entry point
│   ├── index.html               # HTML5 template with SEO meta tags
│   ├── vite.config.js           # Vite dev proxy configuration
│   └── package.json             # Frontend dependencies & scripts
├── tests/                       # Root test runner package
│   ├── __init__.py
│   ├── test_api.py
│   └── test_verify_quotes.py
├── Dockerfile                   # Multi-stage production build (Node + Python)
├── pytest.ini                   # Pytest configuration
├── .gitignore                   # Excludes venv, node_modules, .env, dist
├── .env.example                 # Environment template
└── README.md                    # Project documentation
```

---

<div align="center">

**RentWise — Empowering tenants with transparent, accessible contract intelligence.**

</div>
