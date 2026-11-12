"""Pydantic schemas for the AI Chatbot assistant."""
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User prompt or question")
    document_id: Optional[uuid.UUID] = Field(default=None, description="Optional document context UUID")
    history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Recent conversation turns")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Assistant answer")
    document_id: Optional[uuid.UUID] = Field(default=None, description="Referenced document ID")
    suggested_questions: List[str] = Field(
        default_factory=list,
        description="Follow-up quick question suggestions"
    )
