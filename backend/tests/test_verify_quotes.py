import pytest
from gemini_service import _verify_quotes


def test_verify_quotes_drops_hallucinated_clause():
    """If Gemini's response contains a clause_quote not present in the source text, that flag is dropped."""
    document_text = """
    RENTAL AGREEMENT
    1. The tenant shall pay a monthly rent of Rs 25000 on or before the 5th of every month.
    2. The tenant shall deposit a sum of Rs 250000 as security deposit with the landlord.
    3. The lock-in period shall be 11 months from the commencement date.
    4. The landlord reserves the right to inspect the premises with 24 hours prior notice.
    """

    valid_flag = {
        "clause_quote": "The tenant shall deposit a sum of Rs 250000 as security deposit with the landlord.",
        "risk": "Excessive security deposit amount.",
        "severity": "High",
        "suggestion": "Request reducing security deposit to 2-3 months rent."
    }

    hallucinated_flag = {
        "clause_quote": "The landlord may evict the tenant at any time without assigning any reason or notice.",
        "risk": "Unfair eviction clause.",
        "severity": "High",
        "suggestion": "Delete this clause entirely."
    }

    input_flags = [valid_flag, hallucinated_flag]

    verified = _verify_quotes(input_flags, document_text)

    # Only the valid flag should remain; the hallucinated one must be dropped
    assert len(verified) == 1
    assert verified[0]["clause_quote"] == valid_flag["clause_quote"]
    assert hallucinated_flag not in verified


def test_verify_quotes_handles_case_and_whitespace_normalization():
    """Quotes with differences in whitespace or case are still matched if present in document."""
    document_text = "The   Tenant  shall Pay a   Monthly   Rent of Rs 20000."

    flag = {
        "clause_quote": "The tenant shall pay a monthly rent of Rs 20000.",
        "risk": "Payment schedule",
        "severity": "Low",
        "suggestion": "Check date"
    }

    verified = _verify_quotes([flag], document_text)
    assert len(verified) == 1
    assert verified[0]["clause_quote"] == flag["clause_quote"]


def test_verify_quotes_drops_short_or_empty_quotes():
    """Quotes shorter than or equal to 10 characters are dropped as unreliable."""
    document_text = "The tenant shall pay rent promptly each month without delay."

    too_short_flag = {
        "clause_quote": "rent",
        "risk": "Vague clause",
        "severity": "Low",
        "suggestion": "Clarify"
    }

    empty_quote_flag = {
        "clause_quote": "",
        "risk": "No quote provided",
        "severity": "Medium",
        "suggestion": "Provide quote"
    }

    verified = _verify_quotes([too_short_flag, empty_quote_flag], document_text)
    assert len(verified) == 0


def test_verify_quotes_empty_input():
    """Empty flags list returns empty list."""
    assert _verify_quotes([], "Some rental agreement text here.") == []
