# AGENTRA — API v1 Specification

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  
**Base URL:** `/api/v1`  
**Authentication Scheme:** Bearer JWT in `Authorization` header + HttpOnly Cookie for Refresh  

---

## 1. Global API Standards

### 1.1 Standard Success Envelope
All `2xx` responses are serialized in a standard envelope:
```json
{
  "success": true,
  "data": {},
  "meta": {
    "request_id": "4a737f1e-8fd1-4bc5-83c1-2a91a92e10c7",
    "timestamp": "2026-11-12T10:30:00Z"
  }
}
```

### 1.2 Standard Paginated Envelope
List queries support standard pagination via query parameters `page` (default: 1) and `page_size` (default: 20, max: 100):
```json
{
  "success": true,
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_records": 48,
    "total_pages": 3
  },
  "meta": {
    "request_id": "4a737f1e-8fd1-4bc5-83c1-2a91a92e10c7",
    "timestamp": "2026-11-12T10:30:00Z"
  }
}
```

### 1.3 Standard Error Envelope
All `4xx` and `5xx` responses follow an immutable error schema:
```json
{
  "success": false,
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "The requested document was not found or access is denied.",
    "details": []
  },
  "meta": {
    "request_id": "4a737f1e-8fd1-4bc5-83c1-2a91a92e10c7",
    "timestamp": "2026-11-12T10:30:00Z"
  }
}
```

---

## 2. Authentication Endpoints

### 2.1 `POST /api/v1/auth/register`
- **Description:** Registers a new user account.
- **Auth:** None (Public).
- **Request Body:**
  ```json
  {
    "email": "analyst@enterprise.com",
    "full_name": "Priya Sharma",
    "password": "StrongPassword!2026",
    "role": "USER"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "success": true,
    "data": {
      "user_id": "8f8b8e88-6ef8-490b-b183-b78912ef0011",
      "email": "analyst@enterprise.com",
      "full_name": "Priya Sharma",
      "role": "USER",
      "created_at": "2026-11-12T10:30:00Z"
    }
  }
  ```
- **Errors:** `400 Bad Request` (`AUTH_EMAIL_EXISTS`, `VALIDATION_ERROR`).

---

### 2.2 `POST /api/v1/auth/login`
- **Description:** Authenticates user credentials, sets refresh cookie, returns access token.
- **Auth:** None (Public).
- **Request Body:**
  ```json
  {
    "email": "analyst@enterprise.com",
    "password": "StrongPassword!2026"
  }
  ```
- **Response (200 OK):**
  - **Header:** `Set-Cookie: refresh_token=<opaque_token>; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth; Max-Age=604800`
  ```json
  {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOi...",
      "token_type": "Bearer",
      "expires_in_seconds": 900,
      "user": {
        "id": "8f8b8e88-6ef8-490b-b183-b78912ef0011",
        "email": "analyst@enterprise.com",
        "full_name": "Priya Sharma",
        "role": "USER"
      }
    }
  }
  ```
- **Errors:** `401 Unauthorized` (`AUTH_INVALID_CREDENTIALS`).

---

### 2.3 `POST /api/v1/auth/refresh`
- **Description:** Rotates refresh token from cookie and issues fresh access token.
- **Auth:** Refresh Token Cookie.
- **Response (200 OK):**
  - Fresh cookie rotated via `Set-Cookie`.
  ```json
  {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOi...",
      "token_type": "Bearer",
      "expires_in_seconds": 900
    }
  }
  ```
- **Errors:** `401 Unauthorized` (`AUTH_SESSION_EXPIRED`, `AUTH_SESSION_REVOKED`).

---

### 2.4 `POST /api/v1/auth/logout`
- **Description:** Revokes current refresh session and clears cookie.
- **Auth:** Bearer Access Token or Refresh Cookie.
- **Response (200 OK):**
  - Header: `Set-Cookie: refresh_token=; Max-Age=0; Path=/api/v1/auth`
  ```json
  {
    "success": true,
    "data": { "message": "Successfully logged out." }
  }
  ```

---

### 2.5 `GET /api/v1/auth/me`
- **Description:** Returns profile and role of authenticated user.
- **Auth:** Bearer Access Token.
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "id": "8f8b8e88-6ef8-490b-b183-b78912ef0011",
      "email": "analyst@enterprise.com",
      "full_name": "Priya Sharma",
      "role": "USER"
    }
  }
  ```

---

## 3. Document Endpoints

### 3.1 `POST /api/v1/documents`
- **Description:** Uploads a PDF or DOCX policy file, validates magic bytes, and extracts text.
- **Auth:** Bearer Token (`USER` or `REVIEWER`).
- **Content-Type:** `multipart/form-data`
- **Form Fields:** `file` (Binary file, max 25 MB).
- **Response (201 Created):**
  ```json
  {
    "success": true,
    "data": {
      "id": "d1c08e50-93bf-4d89-9b48-1854bc8c3b01",
      "original_filename": "Global_Expense_Policy_2026.pdf",
      "mime_type": "application/pdf",
      "file_size_bytes": 1048576,
      "page_count": 8,
      "document_status": "READY_FOR_ANALYSIS",
      "created_at": "2026-11-12T10:35:00Z"
    }
  }
  ```
- **Errors:** `400 Bad Request` (`FILE_TOO_LARGE`, `UNSUPPORTED_MEDIA_TYPE`, `FILE_CORRUPTED`, `OCR_REQUIRED`).

---

### 3.2 `GET /api/v1/documents`
- **Description:** Lists documents owned by the user (or all documents for `REVIEWER`).
- **Auth:** Bearer Token.
- **Query Parameters:** `page`, `page_size`, `status` (optional filter).
- **Response (200 OK):** Standard Paginated Envelope of Document summaries.

---

### 3.3 `GET /api/v1/documents/{document_id}`
- **Description:** Returns detailed metadata and extraction status for a single document.
- **Auth:** Bearer Token (Object-level ownership verified).
- **Response (200 OK):** Document detail object including extraction metadata.
- **Errors:** `404 Not Found` (`DOCUMENT_NOT_FOUND`).

---

### 3.4 `DELETE /api/v1/documents/{document_id}`
- **Description:** Soft-deletes a document owned by the user.
- **Auth:** Bearer Token (`USER` owner or `ADMIN`).
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": { "message": "Document successfully soft-deleted." }
  }
  ```
- **Errors:** `404 Not Found` (`DOCUMENT_NOT_FOUND`), `409 Conflict` (`DOCUMENT_HAS_ACTIVE_REVIEWS`).

---

## 4. Analysis Endpoints

### 4.1 `POST /api/v1/documents/{document_id}/analyze`
- **Description:** Initiates controlled agent analysis and deterministic compliance evaluation on a document.
- **Auth:** Bearer Token (Document owner).
- **Response (202 Accepted):**
  ```json
  {
    "success": true,
    "data": {
      "analysis_run_id": "a92e10c7-8fd1-4bc5-83c1-4a737f1e8fd1",
      "document_id": "d1c08e50-93bf-4d89-9b48-1854bc8c3b01",
      "status": "RUNNING",
      "model_name": "gemini-2.5-flash",
      "started_at": "2026-11-12T10:40:00Z"
    }
  }
  ```
- **Errors:** `400 Bad Request` (`DOCUMENT_NOT_READY_FOR_ANALYSIS`), `404 Not Found` (`DOCUMENT_NOT_FOUND`).

---

### 4.2 `GET /api/v1/analyses/{analysis_id}`
- **Description:** Returns the execution state, summary metrics, and status of an analysis run.
- **Auth:** Bearer Token.
- **Response (200 OK):** Analysis details including execution time and completion state.

---

### 4.3 `GET /api/v1/analyses/{analysis_id}/steps`
- **Description:** Returns execution telemetry steps for an analysis run.
- **Auth:** Bearer Token.
- **Response (200 OK):** List of ordered steps ($1 \dots N$) with tool names, duration, and status.

---

### 4.4 `GET /api/v1/analyses/{analysis_id}/findings`
- **Description:** Returns all findings produced by the analysis run.
- **Auth:** Bearer Token.
- **Response (200 OK):** List of findings with evidence quotes and severity.

---

## 5. Findings & Reviews Endpoints

### 5.1 `GET /api/v1/findings`
- **Description:** Lists findings with filters for status and severity.
- **Auth:** Bearer Token.
- **Query Parameters:** `status`, `severity`, `finding_type`, `page`, `page_size`.

---

### 5.2 `GET /api/v1/findings/{finding_id}`
- **Description:** Retrieves finding details, rule reference, and evidence citation.
- **Auth:** Bearer Token.

---

### 5.3 `GET /api/v1/reviews`
- **Description:** Retrieves the review queue of pending tasks.
- **Auth:** Bearer Token (Role: `REVIEWER` or `ADMIN`).
- **Query Parameters:** `status` (default: `OPEN`), `page`, `page_size`.

---

### 5.4 `POST /api/v1/reviews/{review_id}/decision`
- **Description:** Records a human governance decision (`APPROVED`, `REJECTED`, `NEEDS_REVISION`).
- **Auth:** Bearer Token (Role: `REVIEWER`).
- **Request Body:**
  ```json
  {
    "decision": "APPROVED",
    "reviewer_comments": "Verified against Finance Manual Section 4. Limit confirmed."
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "review_task_id": "c1f7a28e-5b1e-4c3d-9f4a-8d1e2f3a4b5c",
      "status": "COMPLETED",
      "decision": "APPROVED",
      "decided_at": "2026-11-12T11:00:00Z"
    }
  }
  ```
- **Errors:** `400 Bad Request` (`REVIEW_COMMENT_REQUIRED_ON_REJECT`, `INVALID_STATE_TRANSITION`), `409 Conflict` (`REVIEW_TASK_ALREADY_DECIDED`).

---

## 6. Audit & System Endpoints

### 6.1 `GET /api/v1/audit-events`
- **Description:** Returns immutable audit logs.
- **Auth:** Bearer Token (Role: `REVIEWER` or `ADMIN`).
- **Query Parameters:** `entity_type`, `entity_id`, `event_type`, `page`, `page_size`.

---

### 6.2 `GET /health`
- **Description:** Liveness probe.
- **Auth:** None.
- **Response (200 OK):**
  ```json
  { "status": "healthy", "service": "agentra-api", "timestamp": "2026-11-12T10:30:00Z" }
  ```

---

### 6.3 `GET /ready`
- **Description:** Readiness probe checking database connectivity and storage directory availability.
- **Auth:** None.
- **Response (200 OK):**
  ```json
  {
    "status": "ready",
    "checks": {
      "database": "connected",
      "storage": "writable"
    }
  }
  ```
