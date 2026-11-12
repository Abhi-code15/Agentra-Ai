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
        """Extracts structured expense policy parameters using Gemini 2.5 Flash.

        Implements exponential backoff with jitter on transient failures and verifies quote provenance.
        """
        user_prompt = build_expense_policy_user_prompt(document_text)

        config = types.GenerateContentConfig(
            system_instruction=EXPENSE_POLICY_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ExpensePolicyExtractionSchema,
            temperature=0.0,
        )

        last_exception = None
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
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
                # Check for fatal unrecoverable errors (e.g. invalid API key)
                err_msg = str(e).lower()
                if "api_key" in err_msg or "invalid argument" in err_msg or "permission denied" in err_msg:
                    logger.error(f"Permanent Gemini API failure on attempt {attempt + 1}: {str(e)}")
                    raise ExternalServiceException(
                        code="AI_PROVIDER_ERROR",
                        message=f"Gemini API authentication or configuration error: {str(e)}",
                    )

                # Exponential backoff with jitter: 1s, 2s, 4s + jitter
                delay = min(8.0, 1.0 * (2 ** attempt)) + random.uniform(0.1, 0.5)
                logger.warning(
                    f"Transient Gemini failure (attempt {attempt + 1}/{max_retries}), retrying in {delay:.2f}s: {str(e)}"
                )
                time.sleep(delay)

        logger.error(f"Exhausted {max_retries} retries calling Gemini: {str(last_exception)}")
        raise ExternalServiceException(
            code="AI_PROVIDER_ERROR",
            message=f"Upstream AI service failed after {max_retries} attempts: {str(last_exception)}",
        )
