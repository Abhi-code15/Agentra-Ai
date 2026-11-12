"""Analysis initiation and execution telemetry API endpoints."""
import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analysis import (
    AnalysisDetailResponse,
    AnalysisInitiateResponse,
    AnalysisStepResponse,
    FindingResponse,
)
from app.schemas.common import SuccessResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(tags=["Analyses"])


@router.post(
    "/documents/{document_id}/analyze",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessResponse[AnalysisInitiateResponse],
)
def analyze_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[AnalysisInitiateResponse]:
    """Initiates controlled agent orchestration and deterministic rule evaluation on a document."""
    service = AnalysisService(db)
    run = service.initiate_analysis(document_id, current_user)

    data = AnalysisInitiateResponse(
        analysis_run_id=run.id,
        document_id=run.document_id,
        status=run.status,
        model_name=run.model_name,
        started_at=run.started_at,
    )
    return SuccessResponse(data=data)


@router.get("/analyses/{analysis_id}", response_model=SuccessResponse[AnalysisDetailResponse])
def get_analysis_detail(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[AnalysisDetailResponse]:
    """Returns execution state, model information, and findings count for an analysis run."""
    service = AnalysisService(db)
    run = service.get_analysis(analysis_id, current_user)
    steps = service.get_analysis_steps(analysis_id, current_user)
    findings = service.get_analysis_findings(analysis_id, current_user)

    detail_data = AnalysisDetailResponse(
        id=run.id,
        document_id=run.document_id,
        requested_by=run.requested_by,
        status=run.status,
        provider=run.provider,
        model_name=run.model_name,
        prompt_version=run.prompt_version,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_code=run.error_code,
        safe_error_message=run.safe_error_message,
        findings_count=len(findings),
        steps_count=len(steps),
    )
    return SuccessResponse(data=detail_data)


@router.get("/analyses/{analysis_id}/steps", response_model=SuccessResponse[List[AnalysisStepResponse]])
def get_analysis_steps(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[List[AnalysisStepResponse]]:
    """Returns execution step history and telemetry for an analysis run."""
    service = AnalysisService(db)
    steps = service.get_analysis_steps(analysis_id, current_user)
    data = [AnalysisStepResponse.model_validate(s) for s in steps]
    return SuccessResponse(data=data)


@router.get("/analyses/{analysis_id}/findings", response_model=SuccessResponse[List[FindingResponse]])
def get_analysis_findings(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[List[FindingResponse]]:
    """Returns all compliance findings identified in an analysis run."""
    service = AnalysisService(db)
    findings = service.get_analysis_findings(analysis_id, current_user)
    data = [FindingResponse.model_validate(f) for f in findings]
    return SuccessResponse(data=data)
