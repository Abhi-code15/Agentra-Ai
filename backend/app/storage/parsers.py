"""Document format validation and page-by-page text extraction engines."""
import io
from typing import Any, Dict, List, Tuple
import docx
import pymupdf

from app.core.exceptions import AgentraException


def validate_magic_bytes(file_bytes: bytes) -> str:
    """Validates file signature magic bytes and returns normalized MIME type."""
    if len(file_bytes) < 5:
        raise AgentraException(
            code="FILE_CORRUPTED",
            message="Uploaded file payload is too short or empty.",
            status_code=400,
        )

    # PDF Magic bytes: %PDF- (0x25 0x50 0x44 0x46 0x2D)
    if file_bytes.startswith(b"%PDF-"):
        return "application/pdf"

    # DOCX Magic bytes: PK\x03\x04 (ZIP container used by OpenXML)
    if file_bytes.startswith(b"PK\x03\x04"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    raise AgentraException(
        code="UNSUPPORTED_MEDIA_TYPE",
        message="Only standard PDF and DOCX files are supported. File header did not match valid signature.",
        status_code=415,
    )


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, int, str, Dict[str, Any]]:
    """Extracts text page-by-page from PDF bytes using PyMuPDF.

    Returns:
        (concatenated_text, page_count, extraction_status, page_metadata)
    """
    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise AgentraException(
            code="FILE_CORRUPTED",
            message=f"Failed to parse PDF document structure: {str(e)}",
            status_code=400,
        )

    page_count = len(doc)
    if page_count == 0:
        return "", 0, "EMPTY", {"pages": []}

    pages_meta: List[Dict[str, Any]] = []
    text_chunks: List[str] = []
    total_characters = 0

    for idx, page in enumerate(doc):
        page_num = idx + 1
        page_text = page.get_text()
        char_count = len(page_text.strip())
        total_characters += char_count

        pages_meta.append({
            "page_number": page_num,
            "character_count": char_count,
            "is_empty": char_count == 0,
        })
        text_chunks.append(f"--- [PAGE {page_num}] ---\n{page_text}")

    full_text = "\n\n".join(text_chunks)

    # Detection of scanned raster image PDFs
    if total_characters == 0:
        return "", page_count, "OCR_REQUIRED", {"pages": pages_meta}

    return full_text, page_count, "COMPLETED", {"pages": pages_meta}


def extract_text_from_docx(file_bytes: bytes) -> Tuple[str, int, str, Dict[str, Any]]:
    """Extracts text from DOCX bytes using python-docx.

    Returns:
        (concatenated_text, estimated_page_count, extraction_status, metadata)
    """
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
    except Exception as e:
        raise AgentraException(
            code="FILE_CORRUPTED",
            message=f"Failed to parse DOCX document structure: {str(e)}",
            status_code=400,
        )

    paragraphs: List[str] = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            paragraphs.append(text)

    # Also extract text from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                paragraphs.append(row_text)

    full_text = "\n\n".join(paragraphs)
    if not full_text.strip():
        return "", 1, "EMPTY", {"paragraph_count": 0}

    # Estimate page count (~3000 chars per page as standard heuristic for docx)
    estimated_pages = max(1, len(full_text) // 3000 + 1)
    return full_text, estimated_pages, "COMPLETED", {"paragraph_count": len(paragraphs)}
