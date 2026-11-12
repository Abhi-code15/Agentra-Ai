"""Deterministic compliance rule evaluation engine."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConditionEvaluationResult(BaseModel):
    field: str
    operator: str
    expected_value: Any
    observed_value: Any
    satisfied: bool
    message: str


class RuleEvaluationResult(BaseModel):
    rule_code: str
    rule_id: Optional[str] = None
    status: str  # PASS, FAIL, INSUFFICIENT_DATA, NEEDS_REVIEW
    condition_results: List[ConditionEvaluationResult] = Field(default_factory=list)
    evidence_quote: Optional[str] = None
    source_page: Optional[int] = None
    explanation: str


class RuleEngine:
    """Pure Python deterministic compliance rule evaluator using an allowlist of operators."""

    SUPPORTED_OPERATORS = {
        "equals",
        "not_equals",
        "greater_than",
        "less_than",
        "greater_than_or_equal",
        "less_than_or_equal",
        "contains",
        "exists",
        "not_exists",
    }

    def evaluate_condition(
        self,
        operator: str,
        observed_value: Any,
        expected_value: Any,
    ) -> bool:
        """Evaluates a single condition using allowlisted deterministic operators."""
        if operator not in self.SUPPORTED_OPERATORS:
            raise ValueError(f"Unsupported compliance operator: {operator}")

        if operator == "exists":
            return observed_value is not None and observed_value != "" and observed_value != []

        if operator == "not_exists":
            return observed_value is None or observed_value == "" or observed_value == []

        if observed_value is None:
            return False

        if operator == "equals":
            return observed_value == expected_value

        if operator == "not_equals":
            return observed_value != expected_value

        if operator == "contains":
            if isinstance(observed_value, (list, tuple, str)):
                return expected_value in observed_value
            return False

        # Numeric comparisons
        try:
            obs_num = float(observed_value)
            exp_num = float(expected_value)
        except (ValueError, TypeError):
            return False

        if operator == "greater_than":
            return obs_num > exp_num
        if operator == "less_than":
            return obs_num < exp_num
        if operator == "greater_than_or_equal":
            return obs_num >= exp_num
        if operator == "less_than_or_equal":
            return obs_num <= exp_num

        return False

    def evaluate_rule(
        self,
        rule_def: Dict[str, Any],
        extracted_data: Dict[str, Any],
        rule_code: str,
        rule_id: Optional[str] = None,
    ) -> RuleEvaluationResult:
        """Evaluates extracted policy parameters against a structured rule definition."""
        target_entity = rule_def.get("target_entity", "approval_tiers")
        field_name = rule_def.get("field", "maximum_amount")
        operator = rule_def.get("operator", "less_than_or_equal")
        expected_value = rule_def.get("expected_value")
        filter_criteria = rule_def.get("filter", {})  # e.g. {"approver_role": "Department Manager"}

        items = extracted_data.get(target_entity, [])
        if not items:
            return RuleEvaluationResult(
                rule_code=rule_code,
                rule_id=rule_id,
                status="INSUFFICIENT_DATA",
                explanation=f"Missing required policy section: {target_entity}",
            )

        # Apply filter if specified
        matched_items = []
        for item in items:
            matches_filter = True
            for filter_key, filter_val in filter_criteria.items():
                val = item.get(filter_key, "")
                if isinstance(val, str) and isinstance(filter_val, str):
                    if filter_val.lower() not in val.lower():
                        matches_filter = False
                        break
                elif val != filter_val:
                    matches_filter = False
                    break
            if matches_filter:
                matched_items.append(item)

        if not matched_items:
            return RuleEvaluationResult(
                rule_code=rule_code,
                rule_id=rule_id,
                status="INSUFFICIENT_DATA",
                explanation=f"No entity matching criteria {filter_criteria} found in {target_entity}.",
            )

        # Evaluate condition on matched item
        target_item = matched_items[0]
        observed_val = target_item.get(field_name)
        quote = target_item.get("evidence_quote")
        page = target_item.get("source_page")

        satisfied = self.evaluate_condition(operator, observed_val, expected_value)

        cond_result = ConditionEvaluationResult(
            field=f"{target_entity}.{field_name}",
            operator=operator,
            expected_value=expected_value,
            observed_value=observed_val,
            satisfied=satisfied,
            message="Condition satisfied" if satisfied else "Condition violated",
        )

        status = "PASS" if satisfied else "FAIL"
        explanation = (
            f"Rule {rule_code} satisfied: Observed {observed_val} {operator} {expected_value}."
            if satisfied
            else f"Rule {rule_code} violated: Observed {observed_val} does not satisfy {operator} {expected_value}."
        )

        return RuleEvaluationResult(
            rule_code=rule_code,
            rule_id=rule_id,
            status=status,
            condition_results=[cond_result],
            evidence_quote=quote,
            source_page=page,
            explanation=explanation,
        )
