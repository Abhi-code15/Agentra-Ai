"""Deterministic evaluation engine comparing employee claims against approved company policy rules."""
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.claim import Claim, ClaimLineItem
from app.models.policy import PolicyRule


class EvaluatedRuleFinding(BaseModel):
    finding_code: str
    rule_id: uuid.UUID
    rule_code: str
    title: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    finding_type: str  # violation, missing_requirement, ambiguity, inconsistency, manual_verification
    confidence_indicator: str = "HIGH"
    evidence: Dict[str, Any] = Field(default_factory=dict)


class ClaimEvaluationOutcome(BaseModel):
    overall_status: str  # PASS, VIOLATION, INSUFFICIENT_DATA, NEEDS_HUMAN_REVIEW
    findings: List[EvaluatedRuleFinding] = Field(default_factory=list)
    summary_message: str


class ClaimEvaluator:
    """Pure deterministic evaluator matching claim parameters against active approved organization policy rules."""

    def evaluate(
        self,
        claim: Claim,
        rules: List[PolicyRule],
    ) -> ClaimEvaluationOutcome:
        findings: List[EvaluatedRuleFinding] = []

        if not rules:
            return ClaimEvaluationOutcome(
                overall_status="NEEDS_HUMAN_REVIEW",
                findings=[
                    EvaluatedRuleFinding(
                        finding_code="NO_ACTIVE_RULES",
                        rule_id=uuid.uuid4(),
                        rule_code="POLICY-UNCONFIGURED",
                        title="No Approved Policy Rules Configured",
                        description="This policy does not have active approved rules. Manual reviewer assessment required.",
                        severity="MEDIUM",
                        finding_type="manual_verification",
                        confidence_indicator="HIGH",
                        evidence={"policy_id": str(claim.policy_id) if claim.policy_id else None},
                    )
                ],
                summary_message="No approved rules configured for this policy version. Queued for human verification.",
            )

        # 1. Evaluate Line Item Category Limits
        for item in claim.line_items:
            category_normalized = item.category.upper()
            for rule in rules:
                rule_def = rule.rule_definition or {}
                source_ref = rule.source_reference or {}
                target_cat = (rule_def.get("target_category") or "").upper()

                if rule.rule_type == "NUMERIC_LIMIT" and (target_cat in category_normalized or category_normalized in target_cat):
                    limit_amt = rule_def.get("limit_amount")
                    if limit_amt is not None and item.amount > float(limit_amt):
                        diff = round(item.amount - float(limit_amt), 2)
                        verbatim = source_ref.get("verbatim_quote", "")
                        findings.append(
                            EvaluatedRuleFinding(
                                finding_code=f"LIMIT_EXCEEDED_{rule.rule_code}",
                                rule_id=rule.id,
                                rule_code=rule.rule_code,
                                title=f"Expense Exceeds Policy Limit: {item.category}",
                                description=(
                                    f"Item '{item.description}' claimed at ${item.amount:.2f} exceeds approved "
                                    f"policy limit of ${float(limit_amt):.2f} (over by ${diff:.2f})."
                                ),
                                severity="HIGH",
                                finding_type="violation",
                                evidence={
                                    "claimed_amount": item.amount,
                                    "policy_limit": float(limit_amt),
                                    "excess_amount": diff,
                                    "item_id": str(item.id),
                                    "policy_citation": verbatim,
                                    "section": source_ref.get("section"),
                                },
                            )
                        )

        # 2. Evaluate Mandatory Documentation (Receipts)
        doc_rules = [r for r in rules if r.rule_type == "MANDATORY_DOCUMENTATION"]
        for rule in doc_rules:
            rule_def = rule.rule_definition or {}
            source_ref = rule.source_reference or {}
            attached_docs = claim.claim_documents or []
            if not attached_docs:
                findings.append(
                    EvaluatedRuleFinding(
                        finding_code=f"DOC_MISSING_{rule.rule_code}",
                        rule_id=rule.id,
                        rule_code=rule.rule_code,
                        title="Mandatory Supporting Document / Receipt Missing",
                        description="Approved policy mandates original receipt/invoice for all reimbursement claims.",
                        severity="HIGH",
                        finding_type="missing_requirement",
                        evidence={
                            "attached_documents_count": 0,
                            "required": rule_def.get("required_documents", ["RECEIPT"]),
                            "policy_citation": source_ref.get("verbatim_quote", ""),
                            "section": source_ref.get("section"),
                        },
                    )
                )

        # 3. Evaluate Submission Timeliness Window
        timeliness_rules = [r for r in rules if r.rule_type == "SUBMISSION_DEADLINE"]
        for rule in timeliness_rules:
            rule_def = rule.rule_definition or {}
            source_ref = rule.source_reference or {}
            max_days = rule_def.get("submission_window_days")
            if max_days and claim.expense_date:
                submission_date = claim.submission_date.date() if isinstance(claim.submission_date, datetime) else claim.submission_date
                days_elapsed = (submission_date - claim.expense_date).days
                if days_elapsed > int(max_days):
                    overdue = days_elapsed - int(max_days)
                    findings.append(
                        EvaluatedRuleFinding(
                            finding_code=f"TIMELINESS_EXCEEDED_{rule.rule_code}",
                            rule_id=rule.id,
                            rule_code=rule.rule_code,
                            title="Claim Submitted Outside Allowable Window",
                            description=(
                                f"Claim submitted {days_elapsed} days post-expense, exceeding the "
                                f"{max_days}-day limit by {overdue} days."
                            ),
                            severity="MEDIUM",
                            finding_type="violation",
                            evidence={
                                "expense_date": str(claim.expense_date),
                                "submission_date": str(submission_date),
                                "days_elapsed": days_elapsed,
                                "max_allowable_days": int(max_days),
                                "policy_citation": source_ref.get("verbatim_quote", ""),
                            },
                        )
                    )

        # Determine overall outcome status
        if any(f.finding_type == "violation" for f in findings):
            overall_status = "VIOLATION"
            summary = f"Claim evaluated with {len(findings)} policy violations."
        elif any(f.finding_type == "missing_requirement" for f in findings):
            overall_status = "INSUFFICIENT_DATA"
            summary = "Claim requires additional documentation before approval."
        elif any(f.finding_type == "manual_verification" for f in findings):
            overall_status = "NEEDS_HUMAN_REVIEW"
            summary = "Claim conforms to basic checks but requires designated reviewer authorization."
        else:
            overall_status = "PASS"
            summary = "All claimed items satisfy approved company standard policy requirements."

        return ClaimEvaluationOutcome(
            overall_status=overall_status,
            findings=findings,
            summary_message=summary,
        )
