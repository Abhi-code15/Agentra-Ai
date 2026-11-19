"""Repository for employee claims, line items, and attached receipts."""
import random
import string
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from app.models.claim import Claim, ClaimDocument, ClaimLineItem


class ClaimRepository:
    """Manages employee claim submissions, line items, and attached receipt proofs."""

    def __init__(self, db: Session):
        self.db = db

    def generate_claim_number(self, claim_type: str = "EXP") -> str:
        prefix = claim_type[:3].upper()
        now_str = datetime.now(timezone.utc).strftime("%Y%m")
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{prefix}-{now_str}-{suffix}"

    def create_claim(
        self,
        organization_id: uuid.UUID,
        employee_id: uuid.UUID,
        claim_type: str,
        title: str,
        description: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        policy_id: Optional[uuid.UUID] = None,
        policy_version_id: Optional[uuid.UUID] = None,
        expense_date: Optional[date] = None,
        total_amount: float = 0.0,
        currency: str = "USD",
        status: str = "SUBMITTED",
    ) -> Claim:
        claim_number = self.generate_claim_number(claim_type)
        claim = Claim(
            organization_id=organization_id,
            employee_id=employee_id,
            claim_type=claim_type,
            claim_number=claim_number,
            title=title,
            description=description,
            department_id=department_id,
            policy_id=policy_id,
            policy_version_id=policy_version_id,
            expense_date=expense_date,
            total_amount=total_amount,
            currency=currency,
            status=status,
            submission_date=datetime.now(timezone.utc),
        )
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def add_line_item(
        self,
        claim_id: uuid.UUID,
        category: str,
        description: str,
        amount: float,
        currency: str = "USD",
        quantity: Optional[int] = None,
        unit: Optional[str] = None,
        transaction_date: Optional[date] = None,
        extracted_data: Optional[Dict[str, Any]] = None,
    ) -> ClaimLineItem:
        item = ClaimLineItem(
            claim_id=claim_id,
            category=category,
            description=description,
            amount=amount,
            currency=currency,
            quantity=quantity,
            unit=unit,
            transaction_date=transaction_date,
            extracted_data=extracted_data or {},
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def attach_document(
        self,
        claim_id: uuid.UUID,
        document_id: uuid.UUID,
        document_type: str = "RECEIPT",
    ) -> ClaimDocument:
        claim_doc = ClaimDocument(
            claim_id=claim_id,
            document_id=document_id,
            document_type=document_type,
        )
        self.db.add(claim_doc)
        self.db.commit()
        self.db.refresh(claim_doc)
        return claim_doc

    def get_claim_by_id(
        self,
        claim_id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
    ) -> Optional[Claim]:
        stmt = (
            select(Claim)
            .options(
                joinedload(Claim.line_items),
                joinedload(Claim.claim_documents),
                joinedload(Claim.findings),
                joinedload(Claim.review_tasks),
                joinedload(Claim.employee),
                joinedload(Claim.policy),
                joinedload(Claim.policy_version),
            )
            .where(Claim.id == claim_id)
        )
        if organization_id:
            stmt = stmt.where(Claim.organization_id == organization_id)
        return self.db.scalars(stmt).first()

    def list_claims_by_org(
        self,
        organization_id: uuid.UUID,
        status: Optional[str] = None,
        claim_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Claim], int]:
        count_stmt = select(func.count(Claim.id)).where(Claim.organization_id == organization_id)
        if status:
            count_stmt = count_stmt.where(Claim.status == status)
        if claim_type:
            count_stmt = count_stmt.where(Claim.claim_type == claim_type)
        total = self.db.scalar(count_stmt) or 0

        stmt = (
            select(Claim)
            .options(
                joinedload(Claim.line_items),
                joinedload(Claim.employee),
                joinedload(Claim.policy),
            )
            .where(Claim.organization_id == organization_id)
        )
        if status:
            stmt = stmt.where(Claim.status == status)
        if claim_type:
            stmt = stmt.where(Claim.claim_type == claim_type)
        stmt = stmt.order_by(Claim.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        return list(self.db.scalars(stmt).unique().all()), total

    def list_claims_by_employee(
        self,
        organization_id: uuid.UUID,
        employee_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Claim], int]:
        count_stmt = select(func.count(Claim.id)).where(
            Claim.organization_id == organization_id,
            Claim.employee_id == employee_id,
        )
        total = self.db.scalar(count_stmt) or 0

        stmt = (
            select(Claim)
            .options(
                joinedload(Claim.line_items),
                joinedload(Claim.policy),
            )
            .where(
                Claim.organization_id == organization_id,
                Claim.employee_id == employee_id,
            )
            .order_by(Claim.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).unique().all()), total

    def update_claim_status(
        self,
        claim_id: uuid.UUID,
        status: str,
        analysis_run_id: Optional[uuid.UUID] = None,
    ) -> Optional[Claim]:
        values: Dict[str, Any] = {"status": status}
        if analysis_run_id:
            values["analysis_run_id"] = analysis_run_id

        self.db.execute(
            update(Claim)
            .where(Claim.id == claim_id)
            .values(**values)
        )
        self.db.commit()
        return self.get_claim_by_id(claim_id)
