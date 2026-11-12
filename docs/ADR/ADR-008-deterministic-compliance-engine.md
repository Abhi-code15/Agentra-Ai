# ADR-008: Deterministic Rule Engine vs LLM-Based Compliance Adjudication

**Status:** Accepted  
**Date:** 2026-11-12  
**Deciders:** Principal System Architect, Quality Assurance Engineer  

---

## 1. Context
A tempting modern anti-pattern is asking an LLM directly: *"Does this document comply with our corporate expense policy? Output yes or no."* This approach fails catastrophically in enterprise governance because LLMs hallucinate numbers, miscalculate tiered boundary conditions (e.g. treating ₹5,001 as ₹5,000), produce inconsistent results on identical prompts, and cannot provide mathematical proof for audit bodies.

## 2. Decision
Enforce a hard **separation of cognitive responsibilities**:
1. **Gemini's Role:** Information extraction, entity recognition, and parsing raw natural language clauses into structured Pydantic data.
2. **Python's Role:** Deterministic compliance evaluation. A pure Python rule engine evaluates arithmetic bounds, threshold tiers, required document presence, and date windows using allowlisted operators (`equals`, `less_than_or_equal`, `greater_than`, `contains`, `exists`).

## 3. Alternatives Considered
- **Pure LLM Prompt Adjudication:** Rejected due to non-determinism, legal liability, and inability to satisfy regulatory audit requirements.
- **Dynamic Python Scripting inside Database:** Rejected. Storing and executing Python code strings (`eval()`) from the database introduces severe remote code execution (RCE) vulnerabilities.

## 4. Consequences
- **Positive:** 100% deterministic, testable, and mathematically reproducible compliance results; zero hallucinated rule outcomes; full compliance with corporate audit requirements.
- **Trade-offs:** Rules must be configured as declarative structured condition trees rather than free-form prose.
