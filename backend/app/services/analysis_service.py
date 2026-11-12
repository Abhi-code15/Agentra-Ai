"""Analysis service orchestrating the agent loop, rule evaluation, and result persistence."""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentOrchestrator
from app.core.exceptions import AgentraException, NotFoundException
from app.core.logging import logger
from app.models.analysis import AnalysisRun, AnalysisStep
from app.models.finding import Finding
from app.models.user import User
from app.repositories.analysis_repo import AnalysisRepository
from app.repositories.document_repo import DocumentRepository


class AnalysisService:
    """Service managing document analysis initiation, agent loops, and finding queries."""

    def __init__(self, db: Session):
        self.db = db
        self.analysis_repo = AnalysisRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.orchestrator = AgentOrchestrator()

    def initiate_analysis(
        self,
        document_id: uuid.UUID,
        current_user: User,
    ) -> AnalysisRun:
        """Initiates bounded agent orchestration on an extracted document."""
        # 1. Verify Document Ownership and Readiness
        owner_filter = current_user.id if current_user.role.upper() == "USER" else None
        document = self.doc_repo.get_by_id(document_id, owner_id=owner_filter)
        if not document:
            raise NotFoundException(
                code="DOCUMENT_NOT_FOUND",
                message="The requested document was not found or access is denied.",
            )

        if document.document_status != "READY_FOR_ANALYSIS":
            raise AgentraException(
                code="DOCUMENT_NOT_READY",
                message=f"Document status '{document.document_status}' is not ready for analysis.",
                status_code=400,
            )

        # 2. Retrieve Extracted Document Text
        extraction = self.doc_repo.get_extraction_by_document_id(document_id)
        if not extraction or not extraction.extracted_text.strip():
            raise AgentraException(
                code="NO_EXTRACTABLE_TEXT",
                message="No extractable text found in this document.",
                status_code=400,
            )

        # 3. Create Analysis Run Record
        analysis_run = self.analysis_repo.create_analysis_run(
            document_id=document_id,
            requested_by=current_user.id,
        )
        self.analysis_repo.update_analysis_status(analysis_run.id, "RUNNING")

        # 4. Fetch Enabled Compliance Rules
        rules = self.analysis_repo.get_enabled_rules(category="EXPENSE_REIMBURSEMENT")
        rules_data = [
            {
                "id": r.id,
                "rule_code": r.rule_code,
                "rule_definition": r.rule_definition,
                "severity": r.severity,
            }
            for r in rules
        ]

        # 5. Execute Agent Orchestration Loop
        try:
            state = self.orchestrator.run_analysis(
                analysis_run_id=analysis_run.id,
                document_id=document_id,
                requested_by=current_user.id,
                raw_document_text=extraction.extracted_text,
                rules=rules_data,
            )

            # 6. Persist Execution Steps Telemetry
            for step_data in state.steps:
                self.analysis_repo.record_step(
                    analysis_run_id=analysis_run.id,
                    step_number=step_data.step_number,
                    step_type=step_data.step_type,
                    tool_name=step_data.tool_name,
                    input_metadata=step_data.input_metadata,
                    output_metadata=step_data.output_metadata,
                    status=step_data.status,
                    duration_ms=step_data.duration_ms,
                    error_code=step_data.error_code,
                )

            # 7. Persist Extracted Items
            for tier in state.extracted_entities.get("approval_tiers", []):
                self.analysis_repo.record_extracted_item(
                    analysis_run_id=analysis_run.id,
                    item_type="APPROVAL_TIER",
                    item_key=tier.get("tier_name", "Tier"),
                    extracted_value=tier,
                    source_page=tier.get("source_page"),
                    evidence_quote=tier.get("evidence_quote"),
                )

            for doc in state.extracted_entities.get("required_documentation", []):
                self.analysis_repo.record_extracted_item(
                    analysis_run_id=analysis_run.id,
                    item_type="REQUIRED_DOCUMENTATION",
                    item_key=doc.get("document_name", "Document"),
                    extracted_value=doc,
                    source_page=doc.get("source_page"),
                    evidence_quote=doc.get("evidence_quote"),
                )

            # 8. Persist Findings & Queue Review Tasks
            for finding in state.generated_findings:
                rule_uuid = uuid.UUID(finding["rule_id"]) if finding.get("rule_id") else None
                self.analysis_repo.create_finding(
                    analysis_run_id=analysis_run.id,
                    finding_code=finding["finding_code"],
                    title=finding["title"],
                    description=finding["description"],
                    severity=finding["severity"],
                    finding_type=finding["finding_type"],
                    evidence=finding["evidence"],
                    rule_id=rule_uuid,
                )

            # 9. Complete Analysis Run
            self.analysis_repo.update_analysis_status(analysis_run.id, "COMPLETED")
            analysis_run.status = "COMPLETED"
            return analysis_run

        except Exception as e:
            logger.exception(f"Analysis run {analysis_run.id} failed: {str(e)}")
            self.analysis_repo.update_analysis_status(
                analysis_run.id,
                status="FAILED",
                error_code="ANALYSIS_RUN_FAILED",
                safe_error_message=str(e),
            )
            analysis_run.status = "FAILED"
            raise AgentraException(
                code="ANALYSIS_EXECUTION_FAILED",
                message=f"Document analysis failed during execution: {str(e)}",
                status_code=500,
            )

    def get_analysis(
        self,
        analysis_id: uuid.UUID,
        current_user: User,
    ) -> AnalysisRun:
        run = self.analysis_repo.get_analysis_run(analysis_id)
        if not run:
            raise NotFoundException(
                code="ANALYSIS_NOT_FOUND",
                message="The requested analysis run was not found.",
            )
        return run

    def get_analysis_steps(
        self,
        analysis_id: uuid.UUID,
        current_user: User,
    ) -> List[AnalysisStep]:
        self.get_analysis(analysis_id, current_user)
        return self.analysis_repo.get_steps_for_run(analysis_id)

    def get_analysis_findings(
        self,
        analysis_id: uuid.UUID,
        current_user: User,
    ) -> List[Finding]:
        self.get_analysis(analysis_id, current_user)
        return self.analysis_repo.get_findings_for_run(analysis_id)
