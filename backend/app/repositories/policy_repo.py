"""Repository for policies, policy versions, and extracted policy rules."""
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from app.models.policy import Policy, PolicyRule, PolicyVersion


class PolicyRepository:
    """Manages company standard policies, immutable versions, and granular verified rules."""

    def __init__(self, db: Session):
        self.db = db

    def create_policy(
        self,
        organization_id: uuid.UUID,
        name: str,
        category: str,
        description: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> Policy:
        policy = Policy(
            organization_id=organization_id,
            name=name,
            category=category,
            description=description,
            department_id=department_id,
            created_by=created_by,
            status="DRAFT",
        )
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def get_policy_by_id(
        self,
        policy_id: uuid.UUID,
        organization_id: Optional[uuid.UUID] = None,
    ) -> Optional[Policy]:
        stmt = (
            select(Policy)
            .options(joinedload(Policy.versions))
            .where(Policy.id == policy_id)
        )
        if organization_id:
            stmt = stmt.where(Policy.organization_id == organization_id)
        return self.db.scalars(stmt).first()

    def list_policies_by_org(
        self,
        organization_id: uuid.UUID,
        category: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Policy], int]:
        count_stmt = select(func.count(Policy.id)).where(Policy.organization_id == organization_id)
        if category:
            count_stmt = count_stmt.where(Policy.category == category)
        if status:
            count_stmt = count_stmt.where(Policy.status == status)
        total = self.db.scalar(count_stmt) or 0

        stmt = (
            select(Policy)
            .options(joinedload(Policy.versions))
            .where(Policy.organization_id == organization_id)
        )
        if category:
            stmt = stmt.where(Policy.category == category)
        if status:
            stmt = stmt.where(Policy.status == status)
        stmt = stmt.order_by(Policy.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        return list(self.db.scalars(stmt).unique().all()), total

    def create_policy_version(
        self,
        policy_id: uuid.UUID,
        version_number: int,
        document_id: Optional[uuid.UUID] = None,
        effective_from: Optional[date] = None,
        effective_until: Optional[date] = None,
        status: str = "DRAFT",
    ) -> PolicyVersion:
        version = PolicyVersion(
            policy_id=policy_id,
            document_id=document_id,
            version_number=version_number,
            effective_from=effective_from,
            effective_until=effective_until,
            status=status,
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def get_version_by_id(self, version_id: uuid.UUID) -> Optional[PolicyVersion]:
        stmt = (
            select(PolicyVersion)
            .options(joinedload(PolicyVersion.rules), joinedload(PolicyVersion.policy), joinedload(PolicyVersion.document))
            .where(PolicyVersion.id == version_id)
        )
        return self.db.scalars(stmt).first()

    def get_active_version(
        self,
        policy_id: uuid.UUID,
        for_date: Optional[date] = None,
    ) -> Optional[PolicyVersion]:
        stmt = (
            select(PolicyVersion)
            .options(joinedload(PolicyVersion.rules))
            .where(
                PolicyVersion.policy_id == policy_id,
                PolicyVersion.status == "ACTIVE",
            )
        )
        if for_date:
            stmt = stmt.where(
                (PolicyVersion.effective_from == None) | (PolicyVersion.effective_from <= for_date),  # noqa: E711
                (PolicyVersion.effective_until == None) | (PolicyVersion.effective_until >= for_date),  # noqa: E711
            )
        stmt = stmt.order_by(PolicyVersion.version_number.desc())
        return self.db.scalars(stmt).first()

    def create_policy_rule(
        self,
        policy_version_id: uuid.UUID,
        rule_code: str,
        name: str,
        description: str,
        category: str,
        rule_type: str,
        rule_definition: Dict[str, Any],
        source_reference: Dict[str, Any],
        extraction_confidence: float = 1.0,
        created_by: Optional[uuid.UUID] = None,
    ) -> PolicyRule:
        rule = PolicyRule(
            policy_version_id=policy_version_id,
            rule_code=rule_code,
            name=name,
            description=description,
            category=category,
            rule_type=rule_type,
            rule_definition=rule_definition,
            source_reference=source_reference,
            extraction_confidence=extraction_confidence,
            verification_status="UNVERIFIED",
            approval_status="PENDING",
            created_by=created_by,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_rule_by_id(self, rule_id: uuid.UUID) -> Optional[PolicyRule]:
        stmt = (
            select(PolicyRule)
            .options(joinedload(PolicyRule.policy_version))
            .where(PolicyRule.id == rule_id)
        )
        return self.db.scalars(stmt).first()

    def list_rules_by_version(self, policy_version_id: uuid.UUID) -> List[PolicyRule]:
        stmt = (
            select(PolicyRule)
            .where(PolicyRule.policy_version_id == policy_version_id)
            .order_by(PolicyRule.category.asc(), PolicyRule.rule_code.asc())
        )
        return list(self.db.scalars(stmt).all())

    def update_rule(
        self,
        rule_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        rule_type: Optional[str] = None,
        rule_definition: Optional[Dict[str, Any]] = None,
        source_reference: Optional[Dict[str, Any]] = None,
        verification_status: Optional[str] = None,
    ) -> Optional[PolicyRule]:
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            return None

        if name is not None:
            rule.name = name
        if description is not None:
            rule.description = description
        if category is not None:
            rule.category = category
        if rule_type is not None:
            rule.rule_type = rule_type
        if rule_definition is not None:
            rule.rule_definition = rule_definition
        if source_reference is not None:
            rule.source_reference = source_reference
        if verification_status is not None:
            rule.verification_status = verification_status
        else:
            rule.verification_status = "MODIFIED"

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def approve_rule(
        self,
        rule_id: uuid.UUID,
        approver_id: uuid.UUID,
        decision: str = "APPROVED",
    ) -> Optional[PolicyRule]:
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            return None

        rule.approval_status = decision
        rule.verification_status = "VERIFIED"
        rule.approved_by = approver_id
        rule.approved_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def activate_version(
        self,
        version_id: uuid.UUID,
        approver_id: uuid.UUID,
    ) -> Optional[PolicyVersion]:
        version = self.get_version_by_id(version_id)
        if not version:
            return None

        # Supersede any previous ACTIVE version of this policy
        self.db.execute(
            update(PolicyVersion)
            .where(
                PolicyVersion.policy_id == version.policy_id,
                PolicyVersion.status == "ACTIVE",
                PolicyVersion.id != version_id,
            )
            .values(status="SUPERSEDED")
        )

        version.status = "ACTIVE"
        version.approved_by = approver_id
        version.approved_at = datetime.now(timezone.utc)

        # Mark parent policy as ACTIVE
        self.db.execute(
            update(Policy)
            .where(Policy.id == version.policy_id)
            .values(status="ACTIVE")
        )

        self.db.commit()
        self.db.refresh(version)
        return version
