# AGENTRA — AI Architecture & Integration Specification

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  
**Provider:** Google Gen AI SDK (`google-genai` / Gemini 2.5 Flash)  

---

## 1. Provider Abstraction Architecture

Agentra isolates all generative AI dependencies behind a dedicated infrastructure layer: `app.integrations.gemini`. The presentation layer and domain services never import or communicate with the Gemini SDK directly.

```mermaid
flowchart LR
    Orchestrator["AgentOrchestrator / ToolExecutor"] -->|ExtractPayload| Parser["GeminiParser"]
    Parser -->|StructuredPrompt| Client["GeminiClient (Adapter)"]
    Client -->|HTTPS + API Key| GoogleSDK["Google Gen AI Python SDK"]
    GoogleSDK -->|gRPC / REST| GeminiAPI["Google Gemini 2.5 Flash API"]
    GeminiAPI -->>|Raw JSON Response| GoogleSDK
    GoogleSDK -->>|Response Object| Client
    Client -->>|Raw Dict| Parser
    Parser -->|Pydantic Model Validation| Orchestrator
```

---

## 2. Model Selection & Configuration

- **Model Identifier:** `gemini-2.5-flash` (or current GA Flash model from Google Gen AI).
- **Rationale:** 
  - Sub-second first-token latency, critical for maintaining interactive agent execution loops.
  - Native Structured Output support (`response_schema`), ensuring rigid adherence to JSON schema.
  - Cost efficiency for large policy documents (hundreds of paragraphs).
  - 1M token context window, eliminating chunking fragmentation for enterprise policies.
- **Generation Parameters:**
  - `temperature: 0.0` (Strictly deterministic extraction; zero creative variance).
  - `top_p: 1.0`
  - `response_mime_type: "application/json"`

---

## 3. Resilience & Retry Strategy

External API calls to Gemini are susceptible to transient network partitions and rate limits (`HTTP 429`, `HTTP 503`).

### Exponential Backoff with Jitter
Every call to Gemini is wrapped in a bounded retry loop:
$$\text{Delay}(attempt) = \min(\text{MaxDelay}, \text{BaseDelay} \times 2^{attempt}) + \text{UniformRandom}(0, \text{Jitter})$$

- `BaseDelay`: 1.0 second.
- `MaxDelay`: 8.0 seconds.
- `MaxAttempts`: 3 attempts.
- **Retryable Errors:** `ConnectionError`, `Timeout`, `ResourceExhausted` (429), `ServiceUnavailable` (503).
- **Non-Retryable Errors:** `InvalidArgument` (400), `PermissionDenied` (403), `NotFound` (404). These fail immediately to prevent resource waste.

---

## 4. Double-Validation Pipeline

Even when Gemini enforces `response_schema` at the API boundary, Agentra never trusts raw JSON as verified truth. All responses pass through a **two-stage verification pipeline**:

1. **Stage 1: Pydantic Syntactic Validation**
   - The returned JSON string is deserialized into typed Pydantic models (`ExpensePolicyExtraction`).
   - Ensures all mandatory fields exist, types match, and arrays conform to bounds.
2. **Stage 2: Deterministic Semantic Provenance Check**
   - For every extracted `evidence_quote`, Python verifies that the substring genuinely exists within the original document extraction text:
     ```python
     if quote not in raw_document_text:
         logger.warning("Hallucinated quote detected in extraction", extra={"quote": quote})
         item.validation_status = "MALFORMED"
     ```
   - Prevents LLM hallucination of non-existent policy clauses.
