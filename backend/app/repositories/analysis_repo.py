"""Repository for analysis runs, execution steps, extracted items, compliance rules, and findings."""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisRun, AnalysisStep, ExtractedItem
from app.models.finding import Finding
from app.models.review import ReviewTask
from app.models.rule import ComplianceRule
from app.rules.default_rules import DEFAULT_COMPLIANCE_RULES


class AnalysisRepository:
    """Handles persistence of agent executions, telemetry steps, compliance rules, and findings."""

    def __init__(self, db: Session):
        self.db = db

    def seed_default_rules(self) -> None:
        """Seeds default compliance rules if not already present."""
        for rule_dict in DEFAULT_COMPLIANCE_RULES:
            stmt = select(ComplianceRule).where(ComplianceRule.rule_code == rule_dict["rule_code"])
            existing = self.db.execute(stmt).scalar_one_or_none()
            if not existing:
                rule = ComplianceRule(
                    rule_code=rule_dict["rule_code"],
                    name=rule_dict["name"],
                    description=rule_dict["description"],
                    category=rule_dict["category"],
                    severity=rule_dict["severity"],
                    rule_definition=rule_dict["rule_definition"],
                    is_enabled=rule_dict["is_enabled"],
                    version=rule_dict["version"],
                )
                self.db.add(rule)
        self.db.commit()

    def get_enabled_rules(self, category: str = "EXPENSE_REIMBURSEMENT") -> List[ComplianceRule]:
        self.seed_default_rules()
        stmt = select(ComplianceRule).where(
            ComplianceRule.is_enabled == True,  # noqa: E712
            ComplianceRule.category == category,
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_analysis_run(
        self,
        document_id: uuid.UUID,
        requested_by: uuid.UUID,
        model_name: str = "gemini-2.5-flash",
    ) -> AnalysisRun:
        run = AnalysisRun(
            document_id=document_id,
            requested_by=requested_by,
            status="INITIALIZED",
            model_name=model_name,
            provider="google_genai",
            prompt_version="v1.0.0",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_analysis_run(self, analysis_id: uuid.UUID) -> Optional[AnalysisRun]:
        stmt = select(AnalysisRun).where(AnalysisRun.id == analysis_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_analysis_status(
        self,
        analysis_id: uuid.UUID,
        status: str,
        error_code: Optional[str] = None,
        safe_error_message: Optional[str] = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(AnalysisRun)
            .where(AnalysisRun.id == analysis_id)
            .values(
                status=status,
                completed_at=now if status in ("COMPLETED", "FAILED") else None,
                error_code=error_code,
                safe_error_message=safe_error_message,
            )
        )
        self.db.execute(stmt)
        self.db.commit()

    def record_step(
        self,
        analysis_run_id: uuid.UUID,
        step_number: int,
        step_type: str,
        tool_name: Optional[str],
        input_metadata: Dict[str, Any],
        output_metadata: Dict[str, Any],
        status: str,
        duration_ms: int,
        error_code: Optional[str] = None,
    ) -> AnalysisStep:
        step = AnalysisStep(
            analysis_run_id=analysis_run_id,
            step_number=step_number,
            step_type=step_type,
            tool_name=tool_name,
            input_metadata=input_metadata,
            output_metadata=output_metadata,
            status=status,
            duration_ms=duration_ms,
            error_code=error_code,
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def record_extracted_item(
        self,
        analysis_run_id: uuid.UUID,
        item_type: str,
        item_key: str,
        extracted_value: Dict[str, Any],
        source_page: Optional[int] = None,
        evidence_quote: Optional[str] = None,
    ) -> ExtractedItem:
        item = ExtractedItem(
            analysis_run_id=analysis_run_id,
            item_type=item_type,
            item_key=item_key,
            extracted_value=extracted_value,
            source_page=source_page,
            evidence_quote=evidence_quote,
            validation_status="VALIDATED",
        )
        self.db.add(item)
        self.db.commit()
        return item

    def create_finding(
        self,
        analysis_run_id: uuid.UUID,
        finding_code: str,
        title: str,
        description: str,
        severity: str,
        finding_type: str,
        evidence: Dict[str, Any],
        rule_id: Optional[uuid.UUID] = None,
    ) -> Finding:
        finding = Finding(
            analysis_run_id=analysis_run_id,
            rule_id=rule_id,
            finding_code=finding_code,
            title=title,
            description=description,
            severity=severity,
            finding_type=finding_type,
            evidence=evidence,
            status="PENDING_REVIEW",
        )
        self.db.add(finding)
        self.db.flush()

        # Queue Review Task for HITL
        task = ReviewTask(
            finding_id=finding.id,
            status="OPEN",
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def get_steps_for_run(self, analysis_id: uuid.UUID) -> List[AnalysisStep]:
        stmt = (
            select(AnalysisStep)
            .where(AnalysisStep.analysis_run_id == analysis_id)
            .order_by(AnalysisStep.step_number.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_findings_for_run(self, analysis_id: uuid.UUID) -> List[Finding]:
        stmt = select(Finding).where(Finding.analysis_run_id == analysis_id)
        return list(self.db.execute(stmt).scalars().all())

    def list_findings(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        finding_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Finding], int]:
        stmt = select(Finding)
        if status:
            stmt = stmt.where(Finding.status == status)
        if severity:
            stmt = stmt.where(Finding.severity == severity)
        if finding_type:
            stmt = stmt.where(Finding.finding_type == finding_type)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_records = self.db.execute(count_stmt).scalar() or 0

        offset = (page - 1) * page_size
        paginated_stmt = stmt.order_by(Finding.created_at.desc()).offset(offset).limit(page_size)
        items = list(self.db.execute(paginated_stmt).scalars().all())
        return items, total_records

    def get_finding_by_id(self, finding_id: uuid.UUID) -> Optional[Finding]:
        stmt = select(Finding).where(Finding.id == finding_id)
        return self.db.execute(stmt).scalar_one_or_none()
