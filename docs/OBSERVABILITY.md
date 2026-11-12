# AGENTRA — Observability & Audit Logging Specification

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  

---

## 1. Observability Architecture

Agentra enforces a strict architectural boundary between **Application Logs** and **Business Audit Events**:

```
+-------------------------------------------------------------------------------------------------------+
|                                    APPLICATION LOGS vs AUDIT EVENTS                                   |
+-------------------------------------------------------------------------------------------------------+
| Application Logs (Stdout / JSON stream)              | Audit Events (PostgreSQL audit_events Table)    |
| - Intended for DevOps & software debugging           | - Intended for Compliance Officers & Auditors |
| - High-volume, short retention (e.g. 14 days)        | - Low-volume, immutable long retention (years)|
| - Formatted as structured JSON to stdout             | - Queryable via secure REST endpoints         |
| - Can be dropped under high load if non-critical     | - Strictly ACID committed in DB transactions  |
+-------------------------------------------------------------------------------------------------------+
```

---

## 2. Structured JSON Log Schema

All stdout log events emitted by the backend adhere to a standardized JSON schema:

```json
{
  "timestamp": "2026-11-12T10:30:00.123Z",
  "level": "INFO",
  "service": "agentra-api",
  "environment": "production",
  "event_name": "document.analysis.completed",
  "request_id": "4a737f1e-8fd1-4bc5-83c1-2a91a92e10c7",
  "user_id": "8f8b8e88-6ef8-490b-b183-b78912ef0011",
  "analysis_run_id": "a92e10c7-8fd1-4bc5-83c1-4a737f1e8fd1",
  "duration_ms": 4215,
  "message": "Analysis run completed successfully. 3 findings generated.",
  "metadata": {
    "model": "gemini-2.5-flash",
    "findings_count": 3
  }
}
```

---

## 3. Correlation ID Propagation

Every incoming HTTP request is assigned a UUID correlation ID by the `CorrelationIdMiddleware`:
1. If incoming header `X-Request-ID` is present and valid UUID, it is adopted; otherwise a fresh `uuid.uuid4()` is generated.
2. The ID is stored in Python `contextvars` to remain accessible across async coroutines.
3. Every log record automatically injects `request_id`.
4. Every outgoing HTTP response includes header `X-Request-ID: <uuid>`.
5. Every `audit_events` row persists `request_id` to allow cross-correlation between compliance records and application logs.

---

## 4. Sensitive Data Redaction Filter

To prevent credential leaks, the custom Python `SensitiveDataFilter` masks values for the following keys in log messages and metadata:
- `password` $\to$ `[REDACTED]`
- `access_token`, `refresh_token`, `token` $\to$ `[REDACTED]`
- `api_key`, `secret_key` $\to$ `[REDACTED]`
- `Authorization` header $\to$ `[REDACTED]`
- Raw policy document text and file stream bytes are never passed to standard loggers.
