<div align="center">

# ClauseCheck

**Rental Agreement Risk Checker for Tenants in India**

Understand your rental agreement before you sign.
Upload your contract, get a plain English breakdown, and know what to ask a lawyer.

---

> **Disclaimer:** This tool provides general information only, not legal advice.
> Always consult a qualified lawyer before signing any agreement.

</div>

---

## The Problem

Millions of tenants in India sign rental agreements without fully understanding the terms. Legal language is hard to read, unfair clauses are easy to miss, and hiring a lawyer to review every agreement is not always practical.

**ClauseCheck bridges that gap.** It gives tenants a clear, jargon-free breakdown of their rental agreement so they can walk into a conversation with their landlord — or their lawyer — informed and prepared.

## Who Is This For?

| Audience | How ClauseCheck Helps |
|---|---|
| First-time renters | Explains what each clause actually means in plain English |
| Tenants relocating to a new city | Flags region-specific unfair practices they may not recognize |
| Anyone before signing | Generates a ready-made checklist of questions for a lawyer |

---

## Features

### 1. Upload or Paste
Upload a PDF rental agreement or paste the full text directly. Text is extracted from PDFs automatically using **pypdf**. If a PDF is scanned (image-only), a clear error is shown.

### 2. Plain English Summary
Get exactly **5 bullet points** summarizing the agreement in simple words — no legal jargon, no ambiguity.

### 3. Red Flag Detection
AI-powered analysis identifies risky or unfair clauses. Each red flag includes:

| Field | Description |
|---|---|
| **Clause Quote** | The exact text copied from your document |
| **Risk** | Why this clause is a problem, in simple language |
| **Severity** | High, Medium, or Low |
| **Suggestion** | What to ask the landlord to change |

Every quoted clause is **verified against the source text** — if a quote doesn't appear in the document, the flag is dropped automatically.

### 4. Ask Questions
A chat interface where you can ask follow-up questions about your document. Answers are grounded **only** in the uploaded text and always cite the relevant clause. If the answer isn't in the document, it says so.

### 5. Lawyer Checklist
A downloadable `.txt` file with specific questions to bring to a qualified lawyer, based on the actual content of your agreement.

---

## Screenshots

*Coming soon*

---

## Architecture

```
┌──────────┐      ┌──────────────┐      ┌────────────────┐
│  Browser  │ ──── │  FastAPI API  │ ──── │  Gemini 2.5    │
│  React    │      │  Python      │      │  Flash         │
└──────────┘      └──────────────┘      └────────────────┘
                         │
                    pypdf (PDF extraction)
                    Pydantic (validation)
```

- **Frontend** — React (Vite) + plain CSS, single-page app
- **Backend** — Python FastAPI with `/analyze`, `/ask`, and `/health` endpoints
- **AI** — Google Gemini API (`gemini-2.5-flash`) via the `google-genai` SDK
- **Storage** — None. No database, no login. Documents processed in memory, never saved.
- **Deploy** — Single Docker container targeting Google Cloud Run

---

## Run Locally

### Prerequisites

- Python 3.12+
- Node.js 18+
- A [Google Gemini API key](https://aistudio.google.com/apikey)

### Backend

```bash
cd backend
python -m venv venv

# Activate virtual environment
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt

# Set your API key
export GEMINI_API_KEY=your-key-here        # macOS / Linux
set GEMINI_API_KEY=your-key-here           # Windows

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Deploy to Google Cloud Run

```bash
# 1. Build and push the Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/clausecheck

# 2. Deploy to Cloud Run
gcloud run deploy clausecheck \
  --image gcr.io/YOUR_PROJECT_ID/clausecheck \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-key-here
```

---

## Project Structure

```
ClauseCheck/
├── backend/
│   ├── main.py                 # FastAPI app with all endpoints
│   ├── models.py               # Pydantic request/response models
│   ├── gemini_service.py       # Gemini API integration + quote verification
│   ├── sample_agreement.py     # Built-in sample for demo purposes
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main React component (single page)
│   │   ├── index.css           # Complete design system
│   │   └── main.jsx            # Entry point
│   ├── index.html              # HTML template with SEO meta tags
│   ├── vite.config.js          # Vite config with API proxy
│   └── package.json
├── Dockerfile                  # Multi-stage build for Cloud Run
├── .env.example                # Environment variable template
├── .gitignore
└── README.md
```

---

## Limitations

| Limitation | Detail |
|---|---|
| **PDF text only** | Scanned documents (images inside PDFs) cannot be read. A clear error is shown. |
| **Not legal advice** | AI may miss issues or misunderstand context. Always consult a lawyer. |
| **No persistence** | Results are not saved. Refreshing the page requires re-uploading. |
| **5 MB file limit** | Large PDFs must be trimmed before uploading. |
| **English only** | Works best with agreements written in English. |
| **AI accuracy** | Clause quotes are verified, but risk assessments are AI-generated and may not cover every scenario. |

---

<div align="center">

**This tool provides general information only, not legal advice.**
**Consult a qualified lawyer before signing any rental agreement.**

</div>
