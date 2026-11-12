"""Review service enforcing reviewer authorization, self-approval prevention, and optimistic locking."""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.core.logging import correlation_id_ctx
from app.models.review import ReviewTask
from app.models.user import User
from app.repositories.analysis_repo import AnalysisRepository
from app.repositories.audit_repo import AuditRepository
from app.repositories.document_repo import DocumentRepository
from app.repositories.review_repo import ReviewRepository
from app.schemas.review import ReviewDecisionRequest


class ReviewService:
    """Service managing human review workflows, impartiality checks, and audit logging."""

    def __init__(self, db: Session):
        self.db = db
        self.review_repo = ReviewRepository(db)
        self.analysis_repo = AnalysisRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.audit_repo = AuditRepository(db)

    def list_reviews(
        self,
        current_user: User,
        status_filter: Optional[str] = "OPEN",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ReviewTask], int]:
        """Lists review queue items (accessible to REVIEWER and ADMIN)."""
        if current_user.role.upper() not in ("REVIEWER", "ADMIN"):
            raise ForbiddenException(
                code="FORBIDDEN_INSUFFICIENT_ROLE",
                message="Only authorized reviewers may access the review queue.",
            )
        return self.review_repo.list_review_tasks(
            status_filter=status_filter,
            page=page,
            page_size=page_size,
        )

    def get_review(
        self,
        review_id: uuid.UUID,
        current_user: User,
    ) -> ReviewTask:
        if current_user.role.upper() not in ("REVIEWER", "ADMIN"):
            raise ForbiddenException(
                code="FORBIDDEN_INSUFFICIENT_ROLE",
                message="Only authorized reviewers may view review tasks.",
            )
        task = self.review_repo.get_review_task_by_id(review_id)
        if not task:
            raise NotFoundException(
                code="REVIEW_NOT_FOUND",
                message="The requested review task was not found.",
            )
        return task

    def decide_review(
        self,
        review_id: uuid.UUID,
        payload: ReviewDecisionRequest,
        current_user: User,
    ) -> ReviewTask:
        """Applies human review decision with conflict detection and audit logging."""
        task = self.get_review(review_id, current_user)

        # Impartiality Check: Reviewer cannot approve findings on documents they uploaded
        finding = task.finding
        if finding:
            analysis_run = self.analysis_repo.get_analysis_run(finding.analysis_run_id)
            if analysis_run:
                document = self.doc_repo.get_by_id(analysis_run.document_id)
                if document and document.owner_id == current_user.id and current_user.role.upper() != "ADMIN":
                    raise ForbiddenException(
                        code="REVIEWER_SELF_APPROVAL_PROHIBITED",
                        message="Compliance violation: Reviewers cannot approve or reject findings on their own uploaded documents.",
                    )

        decision = payload.decision.upper()

        # Optimistic locking execution
        success = self.review_repo.apply_decision_optimistic(
            task_id=task.id,
            finding_id=task.finding_id,
            reviewer_id=current_user.id,
            decision=decision,
            comments=payload.reviewer_comments,
        )

        if not success:
            raise ConflictException(
                code="REVIEW_TASK_ALREADY_DECIDED",
                message="This review task has already been completed by another reviewer.",
            )

        # Audit Event Logging
        req_id_str = correlation_id_ctx.get()
        req_id = uuid.UUID(req_id_str) if req_id_str else uuid.uuid4()

        self.audit_repo.record_event(
            actor_id=current_user.id,
            event_type="REVIEW_DECISION_SUBMITTED",
            entity_type="review_task",
            entity_id=task.id,
            request_id=req_id,
            analysis_run_id=finding.analysis_run_id if finding else None,
            event_metadata={
                "decision": decision,
                "comments": payload.reviewer_comments,
                "reviewer_email": current_user.email,
                "finding_id": str(task.finding_id),
            },
        )

        return self.get_review(review_id, current_user)
