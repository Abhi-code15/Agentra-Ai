"""Controlled Agent Orchestrator managing execution steps, tools, and state transitions."""
import time
import uuid
from typing import Any, Dict, List, Optional

from app.agents.state import AgentState, AgentStepTelemetry
from app.core.exceptions import AgentraException
from app.core.logging import logger
from app.tools.compliance_tools import (
    CreateFindingInput,
    CreateFindingsBatchInput,
    EvaluateRulesInput,
    ExtractDocInfoInput,
    RetrieveEvidenceInput,
    tool_create_review_findings,
    tool_evaluate_compliance_rules,
    tool_extract_document_information,
    tool_retrieve_document_evidence,
)
from app.tools.registry import ToolRegistry


class AgentOrchestrator:
    """Orchestrates bounded, step-by-step document intelligence and rule compliance evaluation."""

    def __init__(self):
        self.registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self) -> None:
        self.registry.register(
            name="extract_document_information",
            description="Extracts structured operational limits and requirements using Gemini",
            input_schema=ExtractDocInfoInput,
            handler=tool_extract_document_information,
        )
        self.registry.register(
            name="retrieve_document_evidence",
            description="Retrieves matching sentences and page locations from document text",
            input_schema=RetrieveEvidenceInput,
            handler=tool_retrieve_document_evidence,
        )
        self.registry.register(
            name="evaluate_compliance_rules",
            description="Evaluates extracted parameters against deterministic compliance rules",
            input_schema=EvaluateRulesInput,
            handler=tool_evaluate_compliance_rules,
        )
        self.registry.register(
            name="create_review_findings",
            description="Formulates and validates compliance findings requiring review",
            input_schema=CreateFindingsBatchInput,
            handler=tool_create_review_findings,
        )

    def _execute_step(
        self,
        state: AgentState,
        step_type: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """Executes a single controlled step with timing, telemetry, and circuit breaker checks."""
        state.current_step += 1
        if state.current_step > state.max_steps:
            raise AgentraException(
                code="STEP_LIMIT_EXCEEDED",
                message=f"Agent exceeded maximum allowed step limit of {state.max_steps}.",
                status_code=500,
            )

        start_time = time.perf_counter()
        telemetry = AgentStepTelemetry(
            step_number=state.current_step,
            step_type=step_type,
            tool_name=tool_name,
            input_metadata={"tool_name": tool_name},
            status="RUNNING",
        )

        try:
            result = self.registry.execute(tool_name, arguments)
            duration_ms = int((time.perf_counter() - start_time) * 1000)

            telemetry.status = "SUCCESS"
            telemetry.duration_ms = duration_ms
            telemetry.output_metadata = {"result_summary": "Completed successfully"}
            state.steps.append(telemetry)
            return result

        except Exception as e:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            telemetry.status = "FAILED"
            telemetry.duration_ms = duration_ms
            telemetry.error_code = getattr(e, "code", "TOOL_EXECUTION_ERROR")
            state.steps.append(telemetry)
            state.errors.append(str(e))
            raise

    def run_analysis(
        self,
        analysis_run_id: uuid.UUID,
        document_id: uuid.UUID,
        requested_by: uuid.UUID,
        raw_document_text: str,
        rules: List[Dict[str, Any]],
    ) -> AgentState:
        """Executes the controlled 4-step analysis workflow on a policy document."""
        state = AgentState(
            analysis_run_id=analysis_run_id,
            document_id=document_id,
            requested_by=requested_by,
            raw_document_text=raw_document_text,
            execution_status="RUNNING",
        )

        try:
            # -----------------------------------------------------------------
            # Step 1: Extract Document Information
            # -----------------------------------------------------------------
            logger.info("Executing Agent Step 1: Information Extraction...")
            extraction_result = self._execute_step(
                state=state,
                step_type="TOOL_EXECUTION",
                tool_name="extract_document_information",
                arguments={"document_text": raw_document_text},
            )
            state.extracted_entities = extraction_result

            # -----------------------------------------------------------------
            # Step 2: Retrieve Relevant Evidence
            # -----------------------------------------------------------------
            logger.info("Executing Agent Step 2: Evidence Retrieval...")
            evidence_result = self._execute_step(
                state=state,
                step_type="TOOL_EXECUTION",
                tool_name="retrieve_document_evidence",
                arguments={
                    "search_query": "approval",
                    "document_text": raw_document_text,
                },
            )
            state.retrieved_evidence = evidence_result

            # -----------------------------------------------------------------
            # Step 3: Evaluate Compliance Rules
            # -----------------------------------------------------------------
            logger.info("Executing Agent Step 3: Deterministic Rule Evaluation...")
            rule_eval_results = self._execute_step(
                state=state,
                step_type="TOOL_EXECUTION",
                tool_name="evaluate_compliance_rules",
                arguments={
                    "extracted_entities": extraction_result,
                    "enabled_rules": rules,
                },
            )
            state.rule_results = rule_eval_results

            # -----------------------------------------------------------------
            # Step 4: Formulate Findings and Review Tasks
            # -----------------------------------------------------------------
            logger.info("Executing Agent Step 4: Finding Formulation...")
            findings_candidates = []

            # 4a. Process rule evaluation failures or missing items
            for eval_res in rule_eval_results:
                rule_status = eval_res.get("status")
                rule_code = eval_res.get("rule_code")

                if rule_status == "FAIL":
                    findings_candidates.append({
                        "finding_code": f"VIOLATION_{rule_code}",
                        "title": f"Rule Violation: {rule_code}",
                        "description": eval_res.get("explanation", "Compliance threshold violation detected."),
                        "severity": "HIGH",
                        "finding_type": "violation",
                        "evidence": {
                            "quote": eval_res.get("evidence_quote"),
                            "page": eval_res.get("source_page"),
                            "condition_results": eval_res.get("condition_results"),
                        },
                        "rule_id": eval_res.get("rule_id"),
                    })

                elif rule_status == "INSUFFICIENT_DATA":
                    findings_candidates.append({
                        "finding_code": f"MISSING_{rule_code}",
                        "title": f"Missing Requirement: {rule_code}",
                        "description": eval_res.get("explanation", "Mandatory policy requirement is missing."),
                        "severity": "MEDIUM",
                        "finding_type": "missing_requirement",
                        "evidence": {
                            "rule_code": rule_code,
                        },
                        "rule_id": eval_res.get("rule_id"),
                    })

            # 4b. Process potential ambiguities flagged by Gemini
            for amb in extraction_result.get("potential_ambiguities", []):
                findings_candidates.append({
                    "finding_code": "AMBIGUOUS_POLICY_CLAUSE",
                    "title": f"Ambiguous Clause: {amb.get('clause_reference', 'General')}",
                    "description": amb.get("description", "Vague or ambiguous clause requiring human clarification."),
                    "severity": amb.get("severity", "MEDIUM"),
                    "finding_type": "ambiguity",
                    "evidence": {
                        "quote": amb.get("evidence_quote"),
                        "page": amb.get("source_page"),
                        "clause": amb.get("clause_reference"),
                    },
                })

            findings_result = self._execute_step(
                state=state,
                step_type="TOOL_EXECUTION",
                tool_name="create_review_findings",
                arguments={"findings": findings_candidates},
            )
            state.generated_findings = findings_result
            state.execution_status = "COMPLETED"
            return state

        except Exception as e:
            state.execution_status = "FAILED"
            state.errors.append(str(e))
            raise
