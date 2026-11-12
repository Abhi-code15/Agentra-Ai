"""Unit tests for document parsers: magic byte validation and PyMuPDF text extraction."""
import pytest
import pymupdf
from app.core.exceptions import AgentraException
from app.storage.parsers import extract_text_from_pdf, validate_magic_bytes


def create_sample_pdf_bytes(text: str = "") -> bytes:
    """Helper creating an in-memory PDF document."""
    doc = pymupdf.open()
    page = doc.new_page()
    if text:
        page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_magic_byte_validation() -> None:
    """Verifies that magic bytes accept valid PDF/DOCX and reject invalid headers."""
    valid_pdf_bytes = b"%PDF-1.7\nSample content"
    assert validate_magic_bytes(valid_pdf_bytes) == "application/pdf"

    valid_docx_bytes = b"PK\x03\x04\x14\x00\x06\x00Sample"
    assert validate_magic_bytes(valid_docx_bytes) == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # Reject arbitrary executable / plain text
    with pytest.raises(AgentraException) as exc:
        validate_magic_bytes(b"MZ\x90\x00\x03\x00\x00\x00")
    assert exc.value.status_code == 415

    # Reject empty payload
    with pytest.raises(AgentraException) as exc:
        validate_magic_bytes(b"")
    assert exc.value.status_code == 400


def test_pymupdf_text_extraction() -> None:
    """Verifies page-by-page extraction from a valid text PDF."""
    policy_text = "Global Expense Reimbursement Policy 2026. Department managers may approve expenses up to INR 5,000."
    pdf_bytes = create_sample_pdf_bytes(policy_text)

    text, page_count, status, metadata = extract_text_from_pdf(pdf_bytes)

    assert status == "COMPLETED"
    assert page_count == 1
    assert "Global Expense Reimbursement Policy" in text
    assert "INR 5,000" in text
    assert len(metadata["pages"]) == 1
    assert metadata["pages"][0]["character_count"] > 0


def test_pymupdf_empty_or_scanned_pdf_detection() -> None:
    """Verifies that a PDF with zero extractable text triggers OCR_REQUIRED status."""
    empty_pdf_bytes = create_sample_pdf_bytes("")  # Blank page with 0 text

    text, page_count, status, metadata = extract_text_from_pdf(empty_pdf_bytes)

    assert status == "OCR_REQUIRED"
    assert page_count == 1
    assert text == ""
    assert metadata["pages"][0]["is_empty"] is True
