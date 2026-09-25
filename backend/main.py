import io
import os
import logging
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pypdf import PdfReader

from models import AnalyzeResponse, AskRequest, AskResponse, RedFlag
from gemini_service import analyze_document, ask_question
from sample_agreement import SAMPLE_AGREEMENT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

app = FastAPI(
    title="ClauseCheck API",
    description="Contract risk checker for tenants in India",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sample")
def get_sample():
    """Return the built-in sample rental agreement."""
    return {"text": SAMPLE_AGREEMENT}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
):
    """Analyze a rental agreement (PDF upload or pasted text)."""
    document_text = ""

    if file and file.filename:
        # Read and validate file
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="File is too large. Maximum size is 5 MB.",
            )

        if file.content_type == "application/pdf" or (
            file.filename and file.filename.lower().endswith(".pdf")
        ):
            try:
                reader = PdfReader(io.BytesIO(contents))
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        document_text += page_text + "\n"
            except Exception as e:
                logger.error(f"PDF parsing failed: {e}")
                raise HTTPException(
                    status_code=400,
                    detail="Could not read this PDF. The file may be corrupted.",
                )

            if not document_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="This PDF does not contain extractable text. It may be a scanned image. Please paste the text manually instead.",
                )
        else:
            # Treat as text file
            try:
                document_text = contents.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Could not read this file as text. Please upload a PDF or paste the agreement text.",
                )

    elif text and text.strip():
        document_text = text.strip()
    else:
        raise HTTPException(
            status_code=400,
            detail="Please upload a file or paste the agreement text.",
        )

    if len(document_text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="The document text is too short to analyze. Please provide the full rental agreement.",
        )

    try:
        result = analyze_document(document_text)
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="The AI service is currently unavailable. Please try again in a moment.",
        )

    return AnalyzeResponse(
        summary=result.get("summary", []),
        red_flags=[RedFlag(**flag) for flag in result.get("red_flags", [])],
        lawyer_questions=result.get("lawyer_questions", []),
        document_text=document_text,
    )


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """Ask a question about the uploaded document."""
    if not request.document_text.strip():
        raise HTTPException(
            status_code=400, detail="No document text provided."
        )
    if not request.question.strip():
        raise HTTPException(
            status_code=400, detail="Please enter a question."
        )
    if len(request.question) > 1000:
        raise HTTPException(
            status_code=400, detail="Question is too long. Please keep it under 1000 characters."
        )

    try:
        result = ask_question(request.document_text, request.question)
    except Exception as e:
        logger.error(f"Gemini ask failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="The AI service is currently unavailable. Please try again in a moment.",
        )

    return AskResponse(
        answer=result.get("answer", "Unable to process your question."),
        source_quote=result.get("source_quote"),
    )


# Serve built frontend in production (Docker)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the React SPA. Falls back to index.html for client-side routing."""
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(static_dir / "index.html")

