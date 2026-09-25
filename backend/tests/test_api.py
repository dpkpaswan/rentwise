import io
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from main import app, MAX_FILE_SIZE, MAX_QUESTION_LENGTH, MAX_DOCUMENT_LENGTH

client = TestClient(app)

SAMPLE_DOC = """
RENTAL AGREEMENT
This Rent Agreement is made and executed at Bengaluru on 1st day of January 2026.
BETWEEN:
Mr. Landlord, residing at Bengaluru, hereinafter called the LESSOR.
AND
Mr. Tenant, residing at Bengaluru, hereinafter called the LESSEE.
1. The tenant shall pay a monthly rent of Rs. 25,000.
2. The tenant shall pay a security deposit of Rs. 2,50,000 equivalent to 10 months rent.
3. The landlord may enter the premises at any time without prior written notice to inspect.
4. The agreement is for a period of 11 months with a mandatory lock-in period of 11 months.
"""


def test_health_returns_200():
    """GET /health returns 200 and ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_empty_text_returns_400_or_422():
    """POST /analyze with empty text returns 400 or 422, not a crash or 500."""
    response = client.post("/analyze", data={"text": ""})
    assert response.status_code in (400, 422)
    assert "detail" in response.json()

    # Also verify whitespace-only text returns 400 or 422
    response_ws = client.post("/analyze", data={"text": "   \n\t   "})
    assert response_ws.status_code in (400, 422)

    # Also verify missing both file and text returns 400 or 422
    response_none = client.post("/analyze", data={})
    assert response_none.status_code in (400, 422)


def test_analyze_valid_sample_returns_200_with_summary_and_flags():
    """POST /analyze with a valid sample returns 200 and includes 'summary' and 'flags' keys."""
    mock_result = {
        "summary": [
            "Monthly rent is Rs. 25,000.",
            "Security deposit is 10 months of rent.",
            "Agreement period is 11 months.",
            "Lock-in period is 11 months.",
            "Landlord claims unrestricted entry rights."
        ],
        "red_flags": [
            {
                "clause_quote": "The tenant shall pay a security deposit of Rs. 2,50,000 equivalent to 10 months rent.",
                "risk": "10 months deposit is excessively high for tenants in India.",
                "severity": "High",
                "suggestion": "Negotiate down to 2-3 months security deposit."
            }
        ],
        "lawyer_questions": [
            "Can the landlord legally enter without prior notice?"
        ]
    }

    with patch("main.analyze_document", return_value=mock_result):
        response = client.post("/analyze", data={"text": SAMPLE_DOC})

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert isinstance(data["summary"], list)
    assert len(data["summary"]) > 0

    # Ensure "flags" key is present as required by the specification
    assert "flags" in data
    assert isinstance(data["flags"], list)
    assert len(data["flags"]) > 0

    # Ensure backward-compatible "red_flags" key is also present for UI
    assert "red_flags" in data
    assert len(data["red_flags"]) > 0
    assert data["red_flags"][0]["clause_quote"] == mock_result["red_flags"][0]["clause_quote"]


def test_analyze_file_oversized_returns_error_not_500():
    """POST /analyze with a file over the size limit returns a proper error (413 or 400), not a 500."""
    oversized_bytes = b"0" * (MAX_FILE_SIZE + 1024)  # 5 MB + 1 KB
    file_payload = ("large_agreement.txt", io.BytesIO(oversized_bytes), "text/plain")

    response = client.post("/analyze", files={"file": file_payload})
    assert response.status_code in (400, 413, 422)
    assert response.status_code != 500
    assert "detail" in response.json()
    assert "large" in response.json()["detail"].lower() or "size" in response.json()["detail"].lower()


def test_analyze_empty_file_returns_error_not_500():
    """POST /analyze with an empty file returns 400 or 422, not 500."""
    file_payload = ("empty.txt", io.BytesIO(b""), "text/plain")
    response = client.post("/analyze", files={"file": file_payload})
    assert response.status_code in (400, 422)
    assert response.status_code != 500


def test_analyze_text_too_short_returns_400():
    """POST /analyze with text under minimum length returns 400."""
    response = client.post("/analyze", data={"text": "Short lease text."})
    assert response.status_code == 400
    assert "short" in response.json()["detail"].lower()


def test_analyze_text_exceeding_max_limit_returns_400():
    """POST /analyze with text exceeding max limit returns 400 to protect AI quotas."""
    huge_text = "Rental agreement clause. " * ((MAX_DOCUMENT_LENGTH // 20) + 10)
    response = client.post("/analyze", data={"text": huge_text})
    assert response.status_code in (400, 422)
    assert response.status_code != 500


def test_ask_valid_document_and_question_returns_200_with_answer():
    """POST /ask with a valid document and question returns 200 and includes an 'answer' key."""
    mock_ask_result = {
        "answer": "The monthly rent is Rs. 25,000 payable each month.",
        "source_quote": "1. The tenant shall pay a monthly rent of Rs. 25,000."
    }

    payload = {
        "document_text": SAMPLE_DOC,
        "question": "How much is the monthly rent?"
    }

    with patch("main.ask_question", return_value=mock_ask_result):
        response = client.post("/ask", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"] == mock_ask_result["answer"]
    assert "source_quote" in data


def test_ask_empty_question_returns_400_or_422():
    """POST /ask with an empty question returns a proper 400 or 422 error."""
    # Test empty string question
    payload_empty = {
        "document_text": SAMPLE_DOC,
        "question": ""
    }
    response = client.post("/ask", json=payload_empty)
    assert response.status_code in (400, 422)
    assert response.status_code != 500

    # Test whitespace-only question
    payload_ws = {
        "document_text": SAMPLE_DOC,
        "question": "     "
    }
    response_ws = client.post("/ask", json=payload_ws)
    assert response_ws.status_code in (400, 422)
    assert response_ws.status_code != 500


def test_ask_empty_document_returns_400_or_422():
    """POST /ask with an empty document returns 400 or 422."""
    payload = {
        "document_text": "",
        "question": "What is the security deposit?"
    }
    response = client.post("/ask", json=payload)
    assert response.status_code in (400, 422)


def test_ask_question_exceeding_max_length_returns_400_or_422():
    """POST /ask with question exceeding 2000 characters returns 400 or 422."""
    payload = {
        "document_text": SAMPLE_DOC,
        "question": "A" * (MAX_QUESTION_LENGTH + 1)
    }
    response = client.post("/ask", json=payload)
    assert response.status_code in (400, 422)
    assert response.status_code != 500


def test_error_response_does_not_leak_internal_stack_trace():
    """Server error responses never contain internal file paths or tracebacks."""
    with patch("main.analyze_document", side_effect=RuntimeError("Internal system failure /var/secret/path")):
        response = client.post("/analyze", data={"text": SAMPLE_DOC})

    assert response.status_code in (500, 502)
    detail = response.json().get("detail", "")
    assert "/var/secret/path" not in detail
    assert "RuntimeError" not in detail
    assert "Traceback" not in detail
