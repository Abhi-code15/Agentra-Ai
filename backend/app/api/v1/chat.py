"""Interactive AI Chatbot endpoint for document intelligence and governance Q&A."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.integrations.gemini.client import GeminiClient
from app.models.user import User
from app.repositories.document_repo import DocumentRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.common import SuccessResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/chat", tags=["AI Chatbot"])


@router.post("", response_model=SuccessResponse[ChatResponse])
def chat_with_assistant(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[ChatResponse]:
    """Provides conversational answers to user questions regarding documents, compliance rules, and policies."""
    document_text = ""
    suggested = [
        "What are the approval thresholds for expenses?",
        "Are receipts mandatory for expenses under ₹5,000?",
        "What expenses are non-reimbursable according to policy?",
        "Summarize the main compliance requirements.",
    ]

    if payload.document_id:
        doc_service = DocumentService(db)
        document = doc_service.get_document(payload.document_id, current_user)
        # Fetch extracted text
        doc_repo = DocumentRepository(db)
        extraction = doc_repo.get_extraction_by_document_id(payload.document_id)
        if extraction and extraction.extracted_text:
            document_text = extraction.extracted_text

        suggested = [
            f"What is the approval limit for {document.original_filename}?",
            "What documentation is required to submit a claim?",
            "Are there any deadlines or time windows for receipts?",
            "Did the compliance scan find any potential violations?",
        ]

    history_dicts = [{"role": m.role, "content": m.content} for m in (payload.history or [])]
    gemini_client = GeminiClient()
    reply = gemini_client.chat_with_document(
        document_text=document_text,
        user_message=payload.message,
        chat_history=history_dicts,
    )

    return SuccessResponse(
        data=ChatResponse(
            reply=reply,
            document_id=payload.document_id,
            suggested_questions=suggested,
        )
    )
