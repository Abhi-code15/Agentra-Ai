"""Agent execution state tracking for controlled orchestration."""
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStepTelemetry(BaseModel):
    step_number: int
    step_type: str
    tool_name: Optional[str] = None
    input_metadata: Dict[str, Any] = Field(default_factory=dict)
    output_metadata: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = 0
    status: str = "PENDING"
    error_code: Optional[str] = None


class AgentState(BaseModel):
    """Explicit typed state tracking an individual document compliance analysis run."""

    analysis_run_id: uuid.UUID
    document_id: uuid.UUID
    requested_by: uuid.UUID
    current_step: int = 0
    max_steps: int = 6
    execution_status: str = "INITIALIZED"  # INITIALIZED, RUNNING, COMPLETED, FAILED

    # Document & Extraction Data
    raw_document_text: str = ""
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    retrieved_evidence: List[Dict[str, Any]] = Field(default_factory=list)

    # Compliance Evaluation
    rule_results: List[Dict[str, Any]] = Field(default_factory=list)
    generated_findings: List[Dict[str, Any]] = Field(default_factory=list)

    # Step History & Telemetry
    steps: List[AgentStepTelemetry] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
