"""Unit tests for the deterministic compliance rule engine."""
import pytest
from app.rules.engine import RuleEngine


def test_rule_engine_operators() -> None:
    """Verifies all supported operators behave deterministically."""
    engine = RuleEngine()

    # Numeric comparisons
    assert engine.evaluate_condition("less_than_or_equal", 5000, 5000) is True
    assert engine.evaluate_condition("less_than_or_equal", 5001, 5000) is False
    assert engine.evaluate_condition("greater_than", 10000, 5000) is True
    assert engine.evaluate_condition("equals", 5000, 5000) is True
    assert engine.evaluate_condition("not_equals", 5001, 5000) is True

    # Existence checks
    assert engine.evaluate_condition("exists", "Some Value", None) is True
    assert engine.evaluate_condition("exists", None, None) is False
    assert engine.evaluate_condition("not_exists", None, None) is True
    assert engine.evaluate_condition("not_exists", "Some Value", None) is False

    # String contains
    assert engine.evaluate_condition("contains", "Department Manager Approval", "Manager") is True
    assert engine.evaluate_condition("contains", "Staff Approval", "Director") is False

    # Unsupported operator raises ValueError
    with pytest.raises(ValueError):
        engine.evaluate_condition("regex_match", "test", "test")


def test_evaluate_rule_pass_condition() -> None:
    """Verifies that rule evaluates to PASS when policy conforms to threshold."""
    engine = RuleEngine()
    rule_def = {
        "target_entity": "approval_tiers",
        "filter": {"approver_role": "Manager"},
        "field": "maximum_amount",
        "operator": "less_than_or_equal",
        "expected_value": 5000.0,
    }

    extracted_data = {
        "approval_tiers": [
            {
                "tier_name": "Tier 1",
                "approver_role": "Department Manager",
                "maximum_amount": 4500.0,
                "evidence_quote": "Managers can approve up to INR 4,500.",
                "source_page": 1,
            }
        ]
    }

    result = engine.evaluate_rule(rule_def, extracted_data, rule_code="EXP_RULE_001")
    assert result.status == "PASS"
    assert len(result.condition_results) == 1
    assert result.condition_results[0].satisfied is True
    assert result.evidence_quote == "Managers can approve up to INR 4,500."


def test_evaluate_rule_fail_condition() -> None:
    """Verifies that rule evaluates to FAIL when policy violates threshold."""
    engine = RuleEngine()
    rule_def = {
        "target_entity": "approval_tiers",
        "filter": {"approver_role": "Manager"},
        "field": "maximum_amount",
        "operator": "less_than_or_equal",
        "expected_value": 5000.0,
    }

    extracted_data = {
        "approval_tiers": [
            {
                "tier_name": "Tier 1",
                "approver_role": "Department Manager",
                "maximum_amount": 7500.0,  # Exceeds 5,000!
                "evidence_quote": "Managers can approve up to INR 7,500.",
                "source_page": 2,
            }
        ]
    }

    result = engine.evaluate_rule(rule_def, extracted_data, rule_code="EXP_RULE_001")
    assert result.status == "FAIL"
    assert result.condition_results[0].satisfied is False
    assert "violated" in result.explanation.lower()


def test_evaluate_rule_insufficient_data() -> None:
    """Verifies that missing policy sections trigger INSUFFICIENT_DATA status."""
    engine = RuleEngine()
    rule_def = {
        "target_entity": "required_documentation",
        "filter": {},
        "field": "is_mandatory",
        "operator": "equals",
        "expected_value": True,
    }

    # Policy completely missing documentation section
    extracted_data = {"approval_tiers": []}

    result = engine.evaluate_rule(rule_def, extracted_data, rule_code="EXP_RULE_DOC")
    assert result.status == "INSUFFICIENT_DATA"
    assert "Missing required policy section" in result.explanation
