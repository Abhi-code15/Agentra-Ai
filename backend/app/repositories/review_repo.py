"""ReviewTask repository with optimistic concurrency control."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from app.models.finding import Finding
from app.models.review import ReviewTask


class ReviewRepository:
    """Repository handling human review tasks and atomic adjudication."""

    def __init__(self, db: Session):
        self.db = db

    def list_review_tasks(
        self,
        status_filter: Optional[str] = "OPEN",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ReviewTask], int]:
        stmt = select(ReviewTask).options(joinedload(ReviewTask.finding))
        if status_filter:
            stmt = stmt.where(ReviewTask.status == status_filter)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_records = self.db.execute(count_stmt).scalar() or 0

        offset = (page - 1) * page_size
        paginated_stmt = stmt.order_by(ReviewTask.created_at.desc()).offset(offset).limit(page_size)
        items = list(self.db.execute(paginated_stmt).scalars().all())

        return items, total_records

    def get_review_task_by_id(self, task_id: uuid.UUID) -> Optional[ReviewTask]:
        stmt = (
            select(ReviewTask)
            .options(joinedload(ReviewTask.finding))
            .where(ReviewTask.id == task_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def apply_decision_optimistic(
        self,
        task_id: uuid.UUID,
        finding_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        decision: str,
        comments: Optional[str],
    ) -> bool:
        """Applies a human review decision using optimistic locking.

        Returns True if successful, False if already adjudicated (status != 'OPEN').
        """
        now = datetime.now(timezone.utc)

        # 1. Atomic update on review_tasks
        task_stmt = (
            update(ReviewTask)
            .where(ReviewTask.id == task_id, ReviewTask.status == "OPEN")
            .values(
                status="COMPLETED",
                decision=decision,
                assigned_reviewer_id=reviewer_id,
                reviewer_comments=comments,
                decided_at=now,
            )
        )
        result = self.db.execute(task_stmt)
        if result.rowcount == 0:
            return False  # Concurrency conflict

        # 2. Update parent finding status
        finding_stmt = (
            update(Finding)
            .where(Finding.id == finding_id)
            .values(status=decision)
        )
        self.db.execute(finding_stmt)
        self.db.commit()
        return True
