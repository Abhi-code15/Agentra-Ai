# ADR-005: Gemini Provider Abstraction Layer

**Status:** Accepted  
**Date:** 2026-11-12  
**Deciders:** Senior AI Engineer, Software Architect  

---

## 1. Context
Directly importing and invoking the Google Gen AI SDK from FastAPI router endpoints or agent tools tightly couples the business layer to a specific vendor's SDK syntax, breaks unit testing, makes mocking painful, and scatters model identifiers across the codebase.

## 2. Decision
Encapsulate all Google Gen AI interactions within a dedicated adapter module: `app.integrations.gemini`. The adapter manages client initialization, structured schema conversion, timeout configuration, bounded retries with jitter, and token tracking.

## 3. Alternatives Considered
- **Direct Router Invocations:** Rejected as an anti-pattern that violates layered clean architecture.
- **LangChain / LlamaIndex Abstractions:** Rejected due to dependency bloat, frequent breaking API changes, black-box debugging difficulty, and unnecessary abstraction layers for an MVP.

## 4. Consequences
- **Positive:** Unit tests can effortlessly mock `GeminiClient` with zero external network traffic; prompt versions and model identifiers are centrally managed; upgrading SDK versions only affects one isolated module.
- **Trade-offs:** Requires writing a custom client adapter, which is minimal (~150 LOC) and significantly cleaner than third-party wrappers.
