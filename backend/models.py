from pydantic import BaseModel, Field
from typing import Optional


class RedFlag(BaseModel):
    clause_quote: str = Field(description="Exact text copied from the document")
    risk: str = Field(description="Why this clause is a problem, in simple words")
    severity: str = Field(description="High, Medium, or Low")
    suggestion: str = Field(description="What the tenant should ask to change")


class AnalyzeResponse(BaseModel):
    summary: list[str] = Field(description="5 bullet points in plain English")
    red_flags: list[RedFlag] = Field(description="List of risky clauses found")
    lawyer_questions: list[str] = Field(description="Questions to ask a lawyer")
    document_text: str = Field(description="Extracted text for follow-up questions")


class AskRequest(BaseModel):
    document_text: str = Field(description="The full document text")
    question: str = Field(description="User's question about the document")


class AskResponse(BaseModel):
    answer: str = Field(description="Answer grounded in the document")
    source_quote: Optional[str] = Field(
        default=None, description="Clause from the document used to answer"
    )


class ErrorResponse(BaseModel):
    detail: str
