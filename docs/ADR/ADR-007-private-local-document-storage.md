# ADR-007: Private Local Filesystem Storage for MVP

**Status:** Accepted  
**Date:** 2026-11-12  
**Deciders:** DevOps Engineer, Application Security Engineer  

---

## 1. Context
Uploading documents to cloud object stores (AWS S3, Google Cloud Storage, Azure Blob) requires cloud credentials, IAM roles, network egress configuration, and local emulation harnesses (MinIO, LocalStack) during development.

## 2. Decision
Use a **Private Local Filesystem Storage Service** (`app.storage.local_storage`) for the MVP:
- Storage root is isolated outside the web public directory (`storage/documents/`).
- Filenames are randomized UUIDs with `.dat` extensions (e.g. `storage/documents/3f8a91bc.dat`).
- File access is strictly gated through authenticated FastAPI streaming endpoints. Direct static URL serving is disabled.

## 3. Alternatives Considered
- **MinIO / LocalStack S3:** Deferred to post-MVP. Introduces unnecessary container dependencies for local developers without altering the storage service abstraction.
- **Direct Database BYTEA Storage:** Rejected due to severe database bloat, backup slowness, and high memory consumption when reading 25 MB documents.

## 4. Consequences
- **Positive:** Zero cloud configuration required for local dev, lightning fast read/write, simple path traversal defense via UUID mapping.
- **Trade-offs:** Horizontal scaling across multiple bare-metal servers requires a shared volume mount (NFS/EFS) or migrating to S3. The storage service interface is designed to make S3 migration a drop-in replacement.
