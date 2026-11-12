"""Implementation of the 4 approved compliance and document tools."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.integrations.gemini.client import GeminiClient
from app.integrations.gemini.schemas import ExpensePolicyExtractionSchema
from app.rules.engine import RuleEngine, RuleEvaluationResult


# ---------------------------------------------------------------------------
# Tool 1: extract_document_information
# ---------------------------------------------------------------------------
class ExtractDocInfoInput(BaseModel):
    document_text: str = Field(description="Raw text of policy document")


def tool_extract_document_information(params: ExtractDocInfoInput) -> Dict[str, Any]:
    """Tool extracting structured operational thresholds and requirements using Gemini."""
    client = GeminiClient()
    extraction = client.extract_structured_policy(params.document_text)
    return extraction.model_dump()


# ---------------------------------------------------------------------------
# Tool 2: retrieve_document_evidence
# ---------------------------------------------------------------------------
class RetrieveEvidenceInput(BaseModel):
    search_query: str = Field(description="Keyword or clause to locate in source document")
    document_text: str = Field(description="Full text of document")


class EvidenceMatch(BaseModel):
    page_number: int
    matching_text: str


def tool_retrieve_document_evidence(params: RetrieveEvidenceInput) -> List[Dict[str, Any]]:
    """Tool searching document text for exact matching sentences or section headings."""
    query = params.search_query.lower()
    matches: List[Dict[str, Any]] = []

    # Parse by page markers "--- [PAGE N] ---"
    pages = params.document_text.split("--- [PAGE ")
    for page_chunk in pages:
        if not page_chunk.strip():
            continue
        try:
            page_header, page_content = page_chunk.split("] ---", 1)
            page_num = int(page_header.strip())
        except Exception:
            page_num = 1
            page_content = page_chunk

        sentences = page_content.split(".")
        for s in sentences:
            if query in s.lower():
                matches.append({
                    "page_number": page_num,
                    "matching_text": s.strip() + ".",
                })

    return matches[:5]  # Return top 5 matches


# ---------------------------------------------------------------------------
# Tool 3: evaluate_compliance_rules
# ---------------------------------------------------------------------------
class EvaluateRulesInput(BaseModel):
    extracted_entities: Dict[str, Any] = Field(description="Parsed policy entities")
    enabled_rules: List[Dict[str, Any]] = Field(description="Configured compliance rules")


def tool_evaluate_compliance_rules(params: EvaluateRulesInput) -> List[Dict[str, Any]]:
    """Tool executing deterministic rule engine against extracted entities."""
    engine = RuleEngine()
    results = []

    for rule in params.enabled_rules:
        outcome = engine.evaluate_rule(
            rule_def=rule.get("rule_definition", {}),
            extracted_data=params.extracted_entities,
            rule_code=rule.get("rule_code", "UNKNOWN_RULE"),
            rule_id=str(rule.get("id")) if rule.get("id") else None,
        )
        results.append(outcome.model_dump())

    return results


# ---------------------------------------------------------------------------
# Tool 4: create_review_finding
# ---------------------------------------------------------------------------
class CreateFindingInput(BaseModel):
    title: str = Field(description="Summary title of finding")
    description: str = Field(description="Detailed compliance explanation")
    severity: str = Field(description="LOW, MEDIUM, HIGH, CRITICAL")
    finding_type: str = Field(description="violation, missing_requirement, ambiguity, inconsistency, manual_verification")
    evidence: Dict[str, Any] = Field(default_factory=dict)
    rule_id: Optional[str] = None
    finding_code: str = Field(default="COMPLIANCE_FINDING")


class CreateFindingsBatchInput(BaseModel):
    findings: List[CreateFindingInput] = Field(description="List of compliance findings to create")


def tool_create_review_findings(params: CreateFindingsBatchInput) -> List[Dict[str, Any]]:
    """Tool formulating a validated batch of findings for persistence and review."""
    return [f.model_dump() for f in params.findings]
