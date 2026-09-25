import json
import os
import logging

from google import genai

logger = logging.getLogger(__name__)

_client = None
MODEL = "gemini-3.8-flash"


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        _client = genai.Client(api_key=api_key)
    return _client


def _call_gemini(prompt: str, retry: bool = True) -> str:
    """Call Gemini and return the text response. Retries once on failure."""
    try:
        response = _get_client().models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        if retry:
            logger.warning(f"Gemini call failed, retrying once: {e}")
            return _call_gemini(prompt, retry=False)
        raise


def _extract_json(text: str) -> any:
    """Extract JSON from a Gemini response that may contain markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


def _verify_quotes(flags: list[dict], document_text: str) -> list[dict]:
    """Drop any red flag whose clause_quote does not appear in the source text."""
    normalized_doc = " ".join(document_text.lower().split())
    verified = []
    for flag in flags:
        quote = flag.get("clause_quote", "")
        normalized_quote = " ".join(quote.lower().split())
        if len(normalized_quote) > 10 and normalized_quote in normalized_doc:
            verified.append(flag)
        else:
            logger.info(f"Dropped unverified flag quote: {quote[:80]}...")
    return verified


def analyze_document(document_text: str) -> dict:
    """Analyze a rental agreement and return summary, red flags, and lawyer questions."""

    prompt = f"""You are a contract review assistant helping an ordinary tenant in India understand a rental agreement. You give general information, not legal advice.

Below is the full text of a rental agreement. Perform these tasks:

TASK 1 - SUMMARY
Write exactly 5 bullet points summarizing the agreement in plain English. Use simple words that a person without legal knowledge can understand. Each bullet should be one sentence.

TASK 2 - RED FLAGS
Identify risky or unfair clauses for the tenant. For each red flag, provide:
- clause_quote: Copy the EXACT text from the document. Do not paraphrase. Do not shorten. The quote must appear verbatim in the document.
- risk: Explain why this is a problem in one or two simple sentences.
- severity: Rate as "High", "Medium", or "Low".
- suggestion: What should the tenant ask the landlord to change.

Check specifically for:
- Unfair deposit terms (excessive amount or unreasonable deduction conditions)
- Unlimited or excessive rent increases
- Landlord entry without notice
- Unclear or unfair notice period
- Penalty clauses
- Unfair maintenance responsibility
- Lock-in period issues
- One-sided eviction terms
- Missing important details
- Waiver of tenant rights

Rules:
- Every flag MUST include an exact quote from the document. If you cannot find an exact quote, do not include that flag.
- Do NOT invent clauses or cite laws unless the law is specifically named in the document.
- Be thorough but only flag genuinely problematic clauses.

TASK 3 - LAWYER QUESTIONS
Write a list of 5-8 specific questions the tenant should ask a qualified lawyer about this agreement. Base these on the actual content of the document.

Return your response as a JSON object with this exact structure:
{{
  "summary": ["bullet 1", "bullet 2", "bullet 3", "bullet 4", "bullet 5"],
  "red_flags": [
    {{
      "clause_quote": "exact text from document",
      "risk": "why this is a problem",
      "severity": "High",
      "suggestion": "what to ask to change"
    }}
  ],
  "lawyer_questions": ["question 1", "question 2"]
}}

Return ONLY the JSON object, no other text.

DOCUMENT:
{document_text}"""

    raw = _call_gemini(prompt)

    try:
        result = _extract_json(raw)
    except json.JSONDecodeError:
        # Retry once with explicit instruction
        logger.warning("Invalid JSON from Gemini, retrying with stricter prompt")
        retry_prompt = prompt + "\n\nIMPORTANT: Your previous response was not valid JSON. Return ONLY a valid JSON object, no markdown, no extra text."
        raw = _call_gemini(retry_prompt, retry=False)
        result = _extract_json(raw)

    # Verify that all clause quotes actually appear in the document
    if "red_flags" in result:
        result["red_flags"] = _verify_quotes(result["red_flags"], document_text)

    return result


def ask_question(document_text: str, question: str) -> dict:
    """Answer a question about the document, grounded only in its text."""

    prompt = f"""You are a contract review assistant. A tenant has uploaded their rental agreement and wants to ask a question about it.

Rules:
- Answer ONLY based on what is written in the document below. Do not use outside knowledge.
- If the answer is in the document, quote the exact clause used to answer.
- If the answer is NOT found in the document, say exactly: "Not found in the document."
- Use simple, plain English. No legal jargon.
- This is general information, not legal advice.

Return your response as a JSON object with this exact structure:
{{
  "answer": "your answer here",
  "source_quote": "exact text from the document used to answer, or null if not found"
}}

Return ONLY the JSON object, no other text.

DOCUMENT:
{document_text}

QUESTION:
{question}"""

    raw = _call_gemini(prompt)

    try:
        result = _extract_json(raw)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON from Gemini ask response, retrying")
        retry_prompt = prompt + "\n\nIMPORTANT: Return ONLY a valid JSON object."
        raw = _call_gemini(retry_prompt, retry=False)
        result = _extract_json(raw)

    return result
