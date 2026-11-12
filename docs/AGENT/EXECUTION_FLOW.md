# AGENTRA — Agent Execution Flow & State Transitions

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  

---

## 1. Step-by-Step Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    participant Orch as AgentOrchestrator
    participant State as AgentState
    participant Registry as ToolRegistry
    participant Tool as ToolExecutor
    participant DB as PostgreSQL
    participant Audit as AuditService

    Orch->>State: Initialize State (run_id, doc_id, max_steps=6)
    Orch->>DB: INSERT analysis_runs (status: RUNNING)

    loop Step Execution (Step 1 to N, Max 6)
        Orch->>State: Increment current_step
        Orch->>Registry: Lookup approved tool for current step
        Registry-->>Orch: Tool instance
        
        Orch->>Tool: Execute tool with typed arguments
        alt Tool Execution Successful
            Tool-->>Orch: ToolOutput (validated schema)
            Orch->>State: Update state with observations
            Orch->>DB: INSERT analysis_steps (status: SUCCESS, duration_ms)
        else Tool Execution Exception / Timeout
            Tool-->>Orch: ToolException
            Orch->>State: Record error
            Orch->>DB: INSERT analysis_steps (status: FAILED, error_code)
            Orch->>DB: UPDATE analysis_runs (status: FAILED)
            Note over Orch: Halt loop on unrecoverable failure
        end
    end

    Orch->>DB: UPDATE analysis_runs (status: COMPLETED, completed_at)
    Orch->>Audit: Log ANALYSIS_COMPLETED event
    Orch-->>Orch: Return final analysis summary
```

---

## 2. Agent State Transition Matrix

| Initial State | Event / Action | Next State | Condition |
| :--- | :--- | :--- | :--- |
| `INITIALIZED` | Orchestrator starts run | `RUNNING` | Document status is `READY_FOR_ANALYSIS` |
| `RUNNING` | Step count exceeds 6 | `FAILED` | Circuit breaker tripped (`STEP_LIMIT_EXCEEDED`) |
| `RUNNING` | Uncaught tool error / Gemini timeout | `FAILED` | Unrecoverable error in tool execution |
| `RUNNING` | All rules evaluated & findings recorded | `COMPLETED` | Normal completion of 4-step pipeline |
| `FAILED` | Post-mortem inspection | `ARCHIVED` | Preserved for engineering analysis |

---

## 3. Tool Sandboxing & Argument Sanitization

Before executing any tool, the `ToolExecutor`:
1. Sanitizes string inputs to prevent SQL injection or path traversal attempts.
2. Validates types using Pydantic (`ValidationError` is caught and converted to an `INVALID_TOOL_ARGUMENT` step failure).
3. Strips sensitive tokens (such as user passwords or API keys) from input/output metadata before storing in `analysis_steps`.
