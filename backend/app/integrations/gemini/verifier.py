"""Quote provenance verification to prevent LLM hallucination of citations."""
import re
from typing import Tuple


def normalize_whitespace(text: str) -> str:
    """Collapses multiple whitespace and newline characters into single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def verify_quote_provenance(quote: str, raw_document_text: str) -> Tuple[bool, str]:
    """Verifies that an extracted quote exists as a verbatim substring in the raw document text.

    Returns:
        (is_valid, validation_status)
    """
    if not quote or not quote.strip():
        return False, "EMPTY_QUOTE"

    # 1. Exact Substring Match
    if quote in raw_document_text:
        return True, "VALIDATED"

    # 2. Normalized Whitespace Substring Match
    normalized_quote = normalize_whitespace(quote)
    normalized_raw = normalize_whitespace(raw_document_text)

    if normalized_quote in normalized_raw:
        return True, "VALIDATED"

    # Hallucination detected
    return False, "UNVERIFIED_CITATION"
