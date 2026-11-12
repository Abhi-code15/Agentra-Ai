"""Default corporate expense reimbursement policy rules."""
from typing import Any, Dict, List

DEFAULT_COMPLIANCE_RULES: List[Dict[str, Any]] = [
    {
        "rule_code": "EXP_RULE_MANAGER_TIER",
        "name": "Department Manager Approval Ceiling",
        "description": "Department managers may only approve operational expense reimbursements up to INR 5,000.",
        "category": "EXPENSE_REIMBURSEMENT",
        "severity": "HIGH",
        "rule_definition": {
            "target_entity": "approval_tiers",
            "filter": {"approver_role": "Manager"},
            "field": "maximum_amount",
            "operator": "less_than_or_equal",
            "expected_value": 5000.0,
        },
        "is_enabled": True,
        "version": 1,
    },
    {
        "rule_code": "EXP_RULE_FINANCE_TIER",
        "name": "Finance Department Approval Ceiling",
        "description": "Expenses between INR 5,001 and INR 10,000 require explicit Finance Department approval.",
        "category": "EXPENSE_REIMBURSEMENT",
        "severity": "HIGH",
        "rule_definition": {
            "target_entity": "approval_tiers",
            "filter": {"approver_role": "Finance"},
            "field": "maximum_amount",
            "operator": "less_than_or_equal",
            "expected_value": 10000.0,
        },
        "is_enabled": True,
        "version": 1,
    },
    {
        "rule_code": "EXP_RULE_RECEIPT_MANDATORY",
        "name": "Mandatory Itemized Receipt / Tax Invoice",
        "description": "Every reimbursement claim must be supported by a mandatory itemized receipt or tax invoice.",
        "category": "EXPENSE_REIMBURSEMENT",
        "severity": "HIGH",
        "rule_definition": {
            "target_entity": "required_documentation",
            "filter": {},
            "field": "is_mandatory",
            "operator": "equals",
            "expected_value": True,
        },
        "is_enabled": True,
        "version": 1,
    },
    {
        "rule_code": "EXP_RULE_SUBMISSION_DEADLINE",
        "name": "Expense Claim Submission Window",
        "description": "Expense reimbursement claims must be submitted within 30 days of spend.",
        "category": "EXPENSE_REIMBURSEMENT",
        "severity": "MEDIUM",
        "rule_definition": {
            "target_entity": "required_documentation",
            "filter": {},
            "field": "submission_window_days",
            "operator": "less_than_or_equal",
            "expected_value": 30,
        },
        "is_enabled": True,
        "version": 1,
    },
]
