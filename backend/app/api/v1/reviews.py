"""Human review queue and decision API endpoints."""
import math
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import RoleChecker, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationMeta, SuccessResponse
from app.schemas.review import ReviewDecisionRequest, ReviewTaskResponse
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("", response_model=PaginatedResponse[ReviewTaskResponse])
def list_review_tasks(
    status: Optional[str] = Query(default="OPEN", description="Filter by status: OPEN, IN_REVIEW, COMPLETED"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(RoleChecker(["REVIEWER", "ADMIN"])),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ReviewTaskResponse]:
    """Returns the review queue of pending tasks (requires REVIEWER or ADMIN role)."""
    service = ReviewService(db)
    items, total_records = service.list_reviews(
        current_user=current_user,
        status_filter=status,
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0
    tasks_data = [ReviewTaskResponse.model_validate(t) for t in items]

    return PaginatedResponse(
        data=tasks_data,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
        ),
    )


@router.get("/{review_id}", response_model=SuccessResponse[ReviewTaskResponse])
def get_review_task(
    review_id: uuid.UUID,
    current_user: User = Depends(RoleChecker(["REVIEWER", "ADMIN"])),
    db: Session = Depends(get_db),
) -> SuccessResponse[ReviewTaskResponse]:
    """Retrieves full details of a review task including evidence citations."""
    service = ReviewService(db)
    task = service.get_review(review_id, current_user)
    return SuccessResponse(data=ReviewTaskResponse.model_validate(task))


@router.post("/{review_id}/decision", response_model=SuccessResponse[ReviewTaskResponse])
def submit_review_decision(
    review_id: uuid.UUID,
    payload: ReviewDecisionRequest,
    current_user: User = Depends(RoleChecker(["REVIEWER", "ADMIN"])),
    db: Session = Depends(get_db),
) -> SuccessResponse[ReviewTaskResponse]:
    """Submits a human governance decision (APPROVED, REJECTED, NEEDS_REVISION) with optimistic locking."""
    service = ReviewService(db)
    updated_task = service.decide_review(review_id, payload, current_user)
    return SuccessResponse(data=ReviewTaskResponse.model_validate(updated_task))
