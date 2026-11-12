# ADR-006: Controlled Bounded Agent Orchestration vs Autonomous Swarms

**Status:** Accepted  
**Date:** 2026-11-12  
**Deciders:** Principal System Architect, Senior AI Engineer  

---

## 1. Context
Autonomous multi-agent swarms (e.g., AutoGen, CrewAI) suffer from non-deterministic execution paths, runaway token consumption, circular reasoning loops, and zero auditable guarantees. Enterprise compliance platforms require predictability, exact step attribution, and strict execution ceilings.

## 2. Decision
Implement a **Controlled Agent Orchestrator** using a typed finite state machine:
- Explicit execution limit of 6 steps per run.
- Pre-registered allowlist of 4 tools with strict Pydantic argument contracts.
- Sandbox validation of all tool inputs and outputs.
- Persistence of every step's status, duration, and telemetry in `analysis_steps`.

## 3. Alternatives Considered
- **LangGraph / CrewAI:** Rejected for MVP. Adds complex runtime overhead and unnecessary graph semantics without improving compliance accuracy.
- **Single-Prompt Zero-Shot Pipeline:** Rejected because document compliance requires multi-stage verification: extraction, targeted evidence retrieval, deterministic rule checking, and finding formulation.

## 4. Consequences
- **Positive:** Guaranteed zero runaway billing or infinite loops, complete step-by-step transparency for human reviewers, fully reproducible execution traces.
- **Trade-offs:** Fixed tool sequence requires explicit code modification if adding new tools. This is a deliberate security feature.
