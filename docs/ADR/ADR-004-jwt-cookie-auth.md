# ADR-004: JWT in Memory with Rotating HttpOnly Refresh Cookies

**Status:** Accepted  
**Date:** 2026-11-12  
**Deciders:** Application Security Engineer, Frontend Lead  

---

## 1. Context
Storing authentication tokens in browser `localStorage` or `sessionStorage` exposes enterprise tokens to Cross-Site Scripting (XSS) extraction attacks. Storing long-lived bearer tokens directly in URLs or insecure cookies is equally vulnerable.

## 2. Decision
Implement a **dual-token authentication strategy**:
1. **Short-Lived Access Tokens (JWT):** Lifetime of 15 minutes, passed in HTTP `Authorization: Bearer <token>` header, held strictly in client JavaScript memory (React state/context). Never written to `localStorage`.
2. **Rotating Refresh Tokens (Opaque):** Lifetime of 7 days, delivered via an `HttpOnly`, `Secure`, `SameSite=Lax` cookie. Stored in PostgreSQL as a SHA-256 hash. Rotated on every refresh invocation. Replay attempts trigger family revocation.

## 3. Alternatives Considered
- **Pure LocalStorage JWT:** Rejected due to OWASP XSS token exfiltration vulnerability.
- **Server-Side Stateful Sessions (Session ID Cookie):** Solid pattern, but requires state check on every micro-call and complicates future mobile or programmatic API client integrations.

## 4. Consequences
- **Positive:** Total immunity to XSS-based refresh token theft; automatic expiration limits window of compromise; refresh rotation immediately catches stolen tokens.
- **Trade-offs:** Page reloads in the browser trigger a silent `/api/v1/auth/refresh` call to restore in-memory access token. This is standard enterprise single-page application practice.
