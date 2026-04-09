"""
Attempt module repository — ALL database queries for attempts and responses.

Rules (CLAUDE.md):
  - ALL DB queries live here. service.py calls this only, never raw SQL.
  - async/await on every DB operation (SQLAlchemy 2.0 async).
  - upsert_response uses INSERT ... ON CONFLICT DO UPDATE.

Public functions consumed by service.py:
  create_attempt
  get_attempt_by_id
  get_ongoing_attempt
  get_attempt_number
  upsert_response
  get_all_responses
  update_attempt_result
  update_last_saved_at
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import case, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attempt.models import Attempt, Response
from app.modules.attempt.schemas import ResponseStateItem


class AttemptRepository:

    # ── Attempt queries ───────────────────────────────────────────────────────

    async def create_attempt(
        self,
        db: AsyncSession,
        *,
        child_profile_id: UUID,
        student_id: UUID | None,
        exam_id: int,
        assignment_id: int | None,
        attempt_number: int,
    ) -> Attempt:
        """Insert a new attempt row with status='ongoing'."""
        attempt = Attempt(
            child_profile_id=child_profile_id,
            student_id=student_id,
            exam_id=exam_id,
            assignment_id=assignment_id,
            attempt_number=attempt_number,
            status="ongoing",
        )
        db.add(attempt)
        await db.flush()          # populate attempt.id before returning
        await db.refresh(attempt)
        return attempt

    async def get_attempt_by_id(
        self, db: AsyncSession, attempt_id: UUID
    ) -> Attempt | None:
        """Return an Attempt by primary key, or None."""
        result = await db.execute(
            select(Attempt).where(Attempt.id == attempt_id)
        )
        return result.scalar_one_or_none()

    async def get_ongoing_attempt(
        self, db: AsyncSession, student_id: UUID, exam_id: int
    ) -> Attempt | None:
        """
        Return the active ongoing attempt for a student+exam, or None.
        Handles two flows:
          - direct-student flow: filters on student_id with child_profile_id IS NULL
          - child_profile_id flow (parent-for-child): filters on child_profile_id
        """
        # Try direct-student path first
        result = await db.execute(
            select(Attempt).where(
                Attempt.student_id == student_id,
                Attempt.child_profile_id == None,
                Attempt.exam_id == exam_id,
                Attempt.status == "ongoing",
            )
        )
        found = result.scalar_one_or_none()
        if found:
            return found
        # Fall through to child_profile_id path (parent-for-child flow)
        result = await db.execute(
            select(Attempt).where(
                Attempt.child_profile_id == student_id,
                Attempt.exam_id == exam_id,
                Attempt.status == "ongoing",
            )
        )
        return result.scalar_one_or_none()

    async def get_attempt_number(
        self, db: AsyncSession, student_id: UUID, exam_id: int
    ) -> int:
        """
        Return the next attempt number for this student+exam.
        Checks both direct-student rows (student_id) and child_profile_id rows.
        Note: student_id param serves dual purpose — it's the student's UUID for
        direct flow, or the child_profile_id for parent-for-child flow.
        """
        # Direct-student rows (student_id set, child_profile_id NULL)
        r1 = await db.execute(
            select(func.count(Attempt.id)).where(
                Attempt.student_id == student_id,
                Attempt.child_profile_id == None,
                Attempt.exam_id == exam_id,
            )
        )
        # Child-profile rows
        r2 = await db.execute(
            select(func.count(Attempt.id)).where(
                Attempt.child_profile_id == student_id,
                Attempt.exam_id == exam_id,
            )
        )
        count = (r1.scalar_one() or 0) + (r2.scalar_one() or 0)
        return count + 1

    async def get_student_attempts(
        self, db: AsyncSession, student_id: UUID, exam_id: int
    ) -> list[Attempt]:
        """Return all attempts for a student+exam (any status), newest first."""
        result = await db.execute(
            select(Attempt).where(
                Attempt.child_profile_id == student_id,
                Attempt.exam_id == exam_id,
            ).order_by(Attempt.attempt_number.desc())
        )
        return list(result.scalars().all())

    async def get_all_student_attempts(
        self, db: AsyncSession, student_id: UUID, limit: int | None = None
    ) -> list[Attempt]:
        """Return all attempts for a student across all exams (any status), newest first."""
        stmt = select(Attempt).where(
            Attempt.child_profile_id == student_id
        ).order_by(Attempt.started_at.desc())
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update_attempt_result(
        self, db: AsyncSession, attempt_id: UUID, result_data: dict
    ) -> Attempt | None:
        """
        Atomic update: sets score fields + JSONB columns + status='submitted'.
        Called by service.submit_exam() after computing scores.
        """
        await db.execute(
            update(Attempt)
            .where(Attempt.id == attempt_id)
            .values(**result_data)
        )
        await db.flush()
        return await self.get_attempt_by_id(db, attempt_id)

    async def update_last_saved_at(
        self, db: AsyncSession, attempt_id: UUID
    ) -> None:
        """
        Lightweight touch — update last_saved_at to now.
        Called after every successful upsert_response().
        Fast: single UPDATE on PK, no SELECT.
        """
        await db.execute(
            update(Attempt)
            .where(Attempt.id == attempt_id)
            .values(last_saved_at=datetime.now(timezone.utc))
        )
        await db.flush()

    # ── Response queries ──────────────────────────────────────────────────────

    async def upsert_response(
        self,
        db: AsyncSession,
        *,
        attempt_id: UUID,
        question_id: int,
        question_no: int,
        selected_option: int | None,
        is_marked_review: bool,
        time_taken_seconds: int | None,
    ) -> Response:
        """
        INSERT ... ON CONFLICT (attempt_id, question_id) DO UPDATE.

        Increment logic:
          - visit_count increments on EVERY upsert (every time student visits question)
          - first_visited_at set only on first insert (stays NULL guard in SQL)
          - answered_at set to now when selected_option is not null
          - selected_option=None clears the answer (student changed mind)

        This is the hottest endpoint on the server — called up to 75 times per exam.
        The ON CONFLICT approach avoids a read-then-write race condition.
        """
        now = datetime.now(timezone.utc)

        stmt = pg_insert(Response).values(
            attempt_id=attempt_id,
            question_id=question_id,
            question_no=question_no,
            selected_option=selected_option,
            is_marked_review=is_marked_review,
            time_taken_seconds=time_taken_seconds,
            first_visited_at=now,
            answered_at=now if selected_option is not None else None,
            visit_count=1,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["attempt_id", "question_id"],
            set_={
                "selected_option": stmt.excluded.selected_option,
                "is_marked_review": stmt.excluded.is_marked_review,
                "time_taken_seconds": stmt.excluded.time_taken_seconds,
                # first_visited_at: keep original (COALESCE preserves first visit)
                "first_visited_at": func.coalesce(
                    Response.first_visited_at, stmt.excluded.first_visited_at
                ),
                # answered_at: update only when an option is selected
                "answered_at": case(
                    (stmt.excluded.selected_option.isnot(None), stmt.excluded.answered_at),
                    else_=Response.answered_at,
                ),
                "visit_count": Response.visit_count + 1,
            }
        ).returning(Response)

        result = await db.execute(stmt)
        await db.flush()
        row = result.fetchone()
        # Reconstruct Response ORM object from returned row
        return await self._get_response(db, attempt_id, question_id)

    async def get_all_responses(
        self, db: AsyncSession, attempt_id: UUID
    ) -> list[Response]:
        """Return all responses for an attempt, ordered by question number."""
        result = await db.execute(
            select(Response)
            .where(Response.attempt_id == attempt_id)
            .order_by(Response.question_no)
        )
        return list(result.scalars().all())

    async def _get_response(
        self, db: AsyncSession, attempt_id: UUID, question_id: int
    ) -> Response:
        """Internal helper to reload a Response after upsert."""
        result = await db.execute(
            select(Response).where(
                Response.attempt_id == attempt_id,
                Response.question_id == question_id,
            )
        )
        return result.scalar_one()


# Module-level singleton
attempt_repository = AttemptRepository()
