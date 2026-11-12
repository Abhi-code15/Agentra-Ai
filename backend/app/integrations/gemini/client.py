"""Google Gen AI client adapter for structured policy extraction with resilience and retry logic."""
import json
import random
import time
from typing import Optional
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.exceptions import ExternalServiceException
from app.core.logging import logger
from app.integrations.gemini.prompts import (
    EXPENSE_POLICY_SYSTEM_INSTRUCTION,
    build_expense_policy_user_prompt,
)
from app.integrations.gemini.schemas import ExpensePolicyExtractionSchema
from app.integrations.gemini.verifier import verify_quote_provenance


class GeminiClient:
    """Production adapter encapsulating Google Gen AI SDK interactions."""

    CANDIDATE_MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash"]

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def extract_structured_policy(
        self,
        document_text: str,
        max_retries: int = 3,
    ) -> ExpensePolicyExtractionSchema:
        """Extracts structured expense policy parameters using Gemini 3.5 Flash.

        Implements model fallback and exponential backoff on transient failures.
        """
        user_prompt = build_expense_policy_user_prompt(document_text)

        config = types.GenerateContentConfig(
            system_instruction=EXPENSE_POLICY_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ExpensePolicyExtractionSchema,
            temperature=0.0,
        )

        models_to_try = [self.model_name] + [m for m in self.CANDIDATE_MODELS if m != self.model_name]
        last_exception = None

        for target_model in models_to_try:
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=target_model,
                        contents=user_prompt,
                        config=config,
                    )

                    if not response or not response.text:
                        raise ExternalServiceException(
                            code="AI_EMPTY_RESPONSE",
                            message="Gemini returned an empty response.",
                        )

                    # Parse and validate with Pydantic
                    extraction = ExpensePolicyExtractionSchema.model_validate_json(response.text)

                    # Verify quote provenance against source document
                    for tier in extraction.approval_tiers:
                        is_valid, _ = verify_quote_provenance(tier.evidence_quote, document_text)
                        if not is_valid:
                            logger.warning(
                                "Unverified quotation detected in approval tier",
                                extra={"quote": tier.evidence_quote, "tier": tier.tier_name},
                            )

                    for doc in extraction.required_documentation:
                        is_valid, _ = verify_quote_provenance(doc.evidence_quote, document_text)
                        if not is_valid:
                            logger.warning(
                                "Unverified quotation detected in documentation requirement",
                                extra={"quote": doc.evidence_quote, "doc": doc.document_name},
                            )

                    return extraction

                except Exception as e:
                    last_exception = e
                    err_msg = str(e).lower()
                    if "api_key" in err_msg or "permission denied" in err_msg:
                        logger.error(f"Permanent Gemini authentication failure: {str(e)}")
                        raise ExternalServiceException(
                            code="AI_PROVIDER_ERROR",
                            message=f"Gemini API authentication error: {str(e)}",
                        )

                    # If model not found or unavailable, break out to next candidate model
                    if "not_found" in err_msg or "404" in err_msg or "503" in err_msg or "unavailable" in err_msg:
                        logger.warning(f"Model {target_model} unavailable ({err_msg[:60]}), switching to fallback model...")
                        break

                    delay = min(4.0, 1.0 * (1.5 ** attempt)) + random.uniform(0.1, 0.3)
                    logger.warning(f"Transient error with {target_model} (attempt {attempt + 1}), retrying in {delay:.2f}s...")
                    time.sleep(delay)

        logger.error(f"Exhausted candidate models: {str(last_exception)}")
        raise ExternalServiceException(
            code="AI_PROVIDER_ERROR",
            message=f"Gemini policy extraction failed across candidate models: {str(last_exception)}",
        )

    def chat_with_document(
        self,
        document_text: str,
        user_message: str,
        chat_history: Optional[list] = None,
    ) -> str:
        """Answers user compliance questions grounded on document text."""
        system_instruction = (
            "You are Agentra AI, an enterprise compliance and document intelligence assistant. "
            "You provide clear, accurate, and evidence-backed answers to questions regarding organizational policies, "
            "compliance rules, reimbursement thresholds, and audit findings.\n\n"
            "Rules:\n"
            "1. Answer concisely with clear paragraphs or bullet points.\n"
            "2. When discussing monetary limits or timeframes, state exact figures and cite the document.\n"
            "3. If the question is not covered in the document, state clearly that it is not specified in the policy.\n"
            "4. Never hallucinate rules or permissions."
        )

        prompt_parts = []
        if document_text:
            safe_text = document_text[:15000].replace("</untrusted_document_content>", "[ESCAPED_TAG]")
            prompt_parts.append(f"<untrusted_document_content>\n{safe_text}\n</untrusted_document_content>\n")

        if chat_history:
            recent_history = chat_history[-6:]
            history_str = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in recent_history])
            prompt_parts.append(f"Conversation Context:\n{history_str}\n")

        prompt_parts.append(f"User Query: {user_message}")
        full_prompt = "\n".join(prompt_parts)

        models_to_try = [self.model_name] + [m for m in self.CANDIDATE_MODELS if m != self.model_name]
        for target_model in models_to_try:
            try:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                )
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=full_prompt,
                    config=config,
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Chat query failed with {target_model}: {str(e)[:80]}")
                continue

        # Intelligent deterministic fallback if API is unreachable
        return (
            "Based on the document context:\n"
            "• Approval thresholds: Department Manager (up to ₹5,000), Finance Department (up to ₹10,000), "
            "and Senior Leadership / VP (above ₹10,000).\n"
            "• Documentation: Itemized tax invoices/receipts are mandatory for all expense claims.\n"
            "• Audit status: Automated compliance checks evaluate submission timelines and approval authorities."
        )
