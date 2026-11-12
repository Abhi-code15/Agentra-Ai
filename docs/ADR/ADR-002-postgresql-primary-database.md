# ADR-002: PostgreSQL as Sole Primary Database

**Status:** Accepted  
**Date:** 2026-11-12  
**Deciders:** Database Architect, Principal System Architect  

---

## 1. Context
Document governance platforms handle relational entities (users, roles, permissions, audit history) alongside semi-structured data (LLM parsed clauses, bounding boxes, telemetry). Engineering teams often introduce multiple databases (MongoDB for JSON, Redis for sessions, PostgreSQL for relations).

## 2. Decision
Use **PostgreSQL 15+ as the sole primary datastore** for relational records, JSONB payloads, session hashes, and audit logs. No secondary databases (Redis, MongoDB) will be introduced in the MVP.

## 3. Alternatives Considered
- **PostgreSQL + Redis:** Deferred. Redis provides in-memory session speed, but refresh session rotation in PostgreSQL is exceptionally fast ($\le 2\text{ms}$) and ensures atomic session management and audit transactions in a single datastore.
- **PostgreSQL + MongoDB:** Rejected. PostgreSQL's native `JSONB` with GIN indexing matches document-database flexibility while maintaining foreign keys to relational entities.

## 4. Consequences
- **Positive:** Single database to backup, monitor, and migrate. Zero distributed cross-database transaction failures. Full ACID guarantees across all tables.
- **Trade-offs:** High-write step telemetry shares connection pool with business transactions. Mitigated with connection pooling and appropriate index tuning.
