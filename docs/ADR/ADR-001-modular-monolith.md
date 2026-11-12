# ADR-001: Adopt Modular Monolith Architecture

**Status:** Accepted  
**Date:** 2026-11-12  
**Deciders:** Principal System Architect, Backend Lead  

---

## 1. Context
Enterprise AI platforms are frequently overengineered into distributed microservices from day zero, introducing network latency, distributed transaction failures, complex container orchestration, and excessive operational cognitive load. For Agentra's MVP, we require high internal cohesion, clear module boundaries, fast iteration speed, and simplified deployment without sacrificing long-term modularity.

## 2. Decision
We will build Agentra as a **Modular Monolith** running within a single FastAPI application process. Internally, the codebase is partitioned into distinct domain modules (`auth`, `documents`, `analyses`, `findings`, `reviews`, `audit`, `rules`, `integrations`) communicating through explicit service interfaces and typed data transfer objects.

## 3. Alternatives Considered
- **Microservices (FastAPI + gRPC + Event Broker):** Rejected due to immense operational complexity, multi-repo overhead, distributed transaction challenges, and zero business need at current scale.
- **Unstructured Monolith (Traditional MVC):** Rejected because global imports and direct database queries in route handlers degrade testability and lead to tight coupling.

## 4. Consequences
- **Positive:** Single process deployment, zero distributed network failure points, atomic database transactions across business domains, rapid local debugging, clean code navigation for developers learning FastAPI.
- **Trade-offs:** Horizontal scaling scales the entire monolith rather than individual hot paths. Mitigated because document analysis and LLM calls are I/O-bound and easily horizontally scalable behind a standard reverse proxy.
