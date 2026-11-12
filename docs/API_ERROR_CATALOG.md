# AGENTRA — API Error Catalog

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  

---

## 1. Error Response Architecture

All error responses adhere to the standard envelope:
```json
{
  "success": false,
  "error": {
    "code": "STRING_ERROR_CODE",
    "message": "Human-readable, client-safe error message.",
    "details": []
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO-8601 UTC"
  }
}
```

---

## 2. Comprehensive Error Catalog

| Error Code | HTTP Status | Client-Safe Message | Cause / Mitigation |
| :--- | :--- | :--- | :--- |
| **`AUTH_INVALID_CREDENTIALS`** | 401 | Invalid email or password. | Credentials did not match. Never disclose whether email exists. |
| **`AUTH_TOKEN_EXPIRED`** | 401 | Access token has expired. Please refresh session. | Access token lifetime (15m) elapsed. Call `/api/v1/auth/refresh`. |
| **`AUTH_TOKEN_INVALID`** | 401 | Authentication token is invalid or malformed. | Token failed cryptographic signature check or claims validation. |
| **`AUTH_SESSION_EXPIRED`** | 401 | Refresh session has expired. Please log in again. | Refresh token session expired (7 days). Re-authenticate. |
| **`AUTH_SESSION_REVOKED`** | 401 | Refresh session has been revoked. | Possible token replay or logout. Revoke session family and re-auth. |
| **`AUTH_EMAIL_EXISTS`** | 400 | An account with this email already exists. | Registration collision on normalized email. |
| **`FORBIDDEN_INSUFFICIENT_ROLE`** | 403 | You do not have permission to perform this action. | User role cannot access reviewer/admin endpoints. |
| **`FORBIDDEN_OBJECT_ACCESS`** | 403 | Access to this resource is prohibited. | Object-level authorization failed (BOLA prevention). |
| **`DOCUMENT_NOT_FOUND`** | 404 | The requested document was not found. | ID does not exist, was soft-deleted, or belongs to another user. |
| **`FILE_TOO_LARGE`** | 400 | Uploaded file exceeds the 25 MB size limit. | Ingested file size > 26,214,400 bytes. Client should compress. |
| **`UNSUPPORTED_MEDIA_TYPE`** | 415 | Only PDF and DOCX documents are supported. | Header magic bytes or MIME type failed validation. |
| **`FILE_CORRUPTED`** | 400 | File is corrupted or unreadable. | PyMuPDF or python-docx failed to parse the file structure. |
| **`OCR_REQUIRED`** | 422 | Document contains scanned images with no extractable text. | PDF text stream is empty. MVP requires text-based PDF or DOCX. |
| **`DOCUMENT_NOT_READY`** | 400 | Document text has not completed extraction. | User triggered analysis before extraction status was `READY`. |
| **`ANALYSIS_NOT_FOUND`** | 404 | The requested analysis run was not found. | Analysis run UUID does not exist. |
| **`ANALYSIS_ALREADY_RUNNING`** | 409 | An analysis run is already in progress for this document. | Prevents redundant duplicate executions on the same document. |
| **`STEP_LIMIT_EXCEEDED`** | 500 | Agent exceeded the maximum execution step limit. | Safety circuit breaker tripped after 6 steps. |
| **`AI_PROVIDER_ERROR`** | 502 | Upstream AI service encountered an error. | Gemini API error after retries were exhausted. |
| **`AI_RATE_LIMIT_EXCEEDED`** | 429 | AI service rate limit reached. Please retry shortly. | HTTP 429 received from Gemini API. |
| **`AI_SCHEMA_VALIDATION_FAILED`**| 502 | AI output failed structural schema validation. | Gemini response failed Pydantic parser schema check. |
| **`FINDING_NOT_FOUND`** | 404 | The requested finding was not found. | Finding UUID does not exist. |
| **`REVIEW_NOT_FOUND`** | 404 | The requested review task was not found. | Review task UUID does not exist. |
| **`REVIEW_TASK_ALREADY_DECIDED`**| 409 | This review task has already been completed. | Concurrent review submission prevented via optimistic locking. |
| **`REVIEW_COMMENT_REQUIRED`** | 400 | Comments are mandatory when rejecting a finding. | Reviewer rejected finding without providing explanatory commentary. |
| **`INVALID_STATE_TRANSITION`** | 400 | The requested status transition is not permitted. | State machine violation (e.g., trying to approve a rejected task). |
| **`VALIDATION_ERROR`** | 422 | Request body failed validation. | Pydantic validation failure on incoming HTTP request body. |
| **`RATE_LIMIT_EXCEEDED`** | 429 | Too many requests. Please slow down. | API rate limit hit on auth or upload endpoints. |
| **`INTERNAL_SERVER_ERROR`** | 500 | An unexpected internal error occurred. | Unhandled system exception. Sanitized error returned to client. |
