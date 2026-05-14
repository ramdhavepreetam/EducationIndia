"""
Attempt module service — business logic for the exam attempt lifecycle.

Rules:
  - Calls repository, catalog_service, question module in sequence.
  - NO raw SQL, NO direct DB access, uses repository only.
  - State changes go through state_machine.transition() only.
  - Score computation is a stub on Day 7; replaced on Day 9.
  - NO correct_option in any return value — scoring is internal only.

Public interface:
  AttemptService.start_exam()         → consumed by router POST /start
  AttemptService.save_response()      → consumed by router POST /{id}/responses
  AttemptService.get_exam_state()     → consumed by router GET /{id}/state
  AttemptService.submit_exam()        → consumed by router POST /{id}/submit
  AttemptService.get_student_attempts()→ consumed by router GET /
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attempt.repository import attempt_repository
from app.modules.attempt.schemas import (
    AttemptResultResponse,
    AttemptStateResponse,
    AttemptSummary,
    ResponseStateItem,
    SaveResponseRequest,
    StartAttemptRequest,
)
from app.modules.attempt.state_machine import (
    AttemptAlreadySubmittedException,
    transition,
)
from app.modules.catalog.service import catalog_service
from app.shared.exceptions import BadRequest, Conflict, Forbidden, NotFound


class AttemptService:

    # ── Start exam ────────────────────────────────────────────────────────────

    async def start_exam(
        self,
        db: AsyncSession,
        parent_id: UUID,
        request: StartAttemptRequest,
    ) -> AttemptStateResponse:
        """
        Start a new exam attempt.

        Validation sequence:
          1. Exam must exist and be is_active (raises NotFound otherwise)
          2. No ongoing attempt already exists for this student+exam
          3. If assignment_id given: validate assignment exists, is_active,
             max_attempts not exceeded, and valid_until not past

        Returns full AttemptStateResponse with empty responses list
        and time_remaining_seconds = exam.duration_minutes * 60.

        Raises:
          NotFound if exam doesn't exist or is inactive
          Conflict if an ongoing attempt already exists
        """
        # 1. Validate exam is active
        exam = await catalog_service.get_active_exam(db, request.exam_id)

        # 1.5 Resolve effective student ID
        if request.child_profile_id is not None:
            from app.modules.user.child_repository import child_repository as child_repo
            is_owner = await child_repo.validate_ownership(
                request.child_profile_id, parent_id, db
            )
            if not is_owner:
                raise Forbidden("Child profile not found")
            effective_student_id = request.child_profile_id
        else:
            effective_student_id = parent_id   # caller IS the student

        # 1.6 Access control gate (ADR-014)
        from app.shared.access_control import get_access_context, can_start_exam as check_start
        ctx = await get_access_context(parent_id, db)
        allowed, reason = await check_start(ctx, request.exam_id, effective_student_id, db)
        if not allowed:
            raise Forbidden(reason)

        # 2. Ensure no duplicate ongoing attempt
        existing = await attempt_repository.get_ongoing_attempt(
            db, effective_student_id, request.exam_id
        )
        if existing is not None:
            raise Conflict(
                f"You already have an ongoing attempt (id: {existing.id}) for this exam. "
                "Resume it via GET /api/attempts/{attempt_id}/state or submit it first."
            )

        # 3. Validate assignment if provided
        if request.assignment_id is not None:
            await self._validate_assignment(db, request.assignment_id, effective_student_id)

        # 4. Create attempt — set student_id for direct flow so DB trigger fires
        attempt_number = await attempt_repository.get_attempt_number(
            db, effective_student_id, request.exam_id
        )
        is_direct = request.child_profile_id is None
        attempt = await attempt_repository.create_attempt(
            db,
            child_profile_id=request.child_profile_id,
            student_id=parent_id if is_direct else None,
            exam_id=request.exam_id,
            assignment_id=request.assignment_id,
            attempt_number=attempt_number,
        )

        time_remaining = exam.duration_minutes * 60

        return AttemptStateResponse(
            attempt_id=attempt.id,
            exam_id=attempt.exam_id,
            attempt_number=attempt.attempt_number,
            status=str(attempt.status.value if hasattr(attempt.status, "value") else attempt.status),
            started_at=attempt.started_at,
            time_remaining_seconds=time_remaining,
            responses=[],
        )

    # ── Save response (autosave) ───────────────────────────────────────────────

    async def save_response(
        self,
        db: AsyncSession,
        attempt_id: UUID,
        student_id: UUID,
        request: SaveResponseRequest,
    ) -> ResponseStateItem:
        """
        Upsert one question response (autosave).

        Validation:
          - Attempt must belong to this student
          - Attempt must be 'ongoing'
          - Timer must not be exceeded

        This is the hottest endpoint (up to 75 calls/exam). Kept lean:
        only one DB read (get_attempt_by_id) + one upsert + one touch.

        Raises:
          NotFound if attempt not found
          Forbidden if attempt belongs to another student
          Forbidden if attempt is not ongoing (already submitted/expired)
          BadRequest if timer exceeded
        """
        attempt = await self._get_owned_attempt(db, attempt_id, student_id)
        self._assert_ongoing(attempt)
        await self._assert_timer_valid(db, attempt)

        response = await attempt_repository.upsert_response(
            db,
            attempt_id=attempt_id,
            question_id=request.question_id,
            question_no=await self._get_question_no(db, request.question_id),
            selected_option=request.selected_option,
            selected_options=request.selected_options,
            is_marked_review=request.is_marked_review,
            time_taken_seconds=request.time_taken_seconds,
        )

        await attempt_repository.update_last_saved_at(db, attempt_id)

        return ResponseStateItem(
            question_no=response.question_no,
            question_id=response.question_id,
            selected_option=response.selected_option,
            selected_options=response.selected_options,
            is_marked_review=response.is_marked_review,
            visit_count=response.visit_count,
        )

    # ── Get exam state (resume) ───────────────────────────────────────────────

    async def get_exam_state(
        self,
        db: AsyncSession,
        attempt_id: UUID,
        student_id: UUID,
    ) -> AttemptStateResponse:
        """
        Return full attempt state for page resume.

        If the timer has elapsed and status is still 'ongoing', auto-transition
        to 'expired' before returning (handles browser-close edge case).

        Raises:
          NotFound if attempt not found
          Forbidden if attempt belongs to another student
        """
        attempt = await self._get_owned_attempt(db, attempt_id, student_id)

        # Load exam once — used for both auto-expire check and time remaining
        try:
            exam = await catalog_service.get_exam(db, attempt.exam_id)
            duration_minutes = exam.duration_minutes
        except Exception:
            duration_minutes = 90

        # Auto-expire if timer ran out
        current_status = str(attempt.status.value if hasattr(attempt.status, "value") else attempt.status)
        if current_status == "ongoing":
            remaining = self._compute_time_remaining(attempt, duration_minutes)
            if remaining <= 0:
                attempt = await transition(attempt, "expired", db)

        # Re-read status from (possibly mutated) attempt object
        current_status = str(attempt.status.value if hasattr(attempt.status, "value") else attempt.status)

        time_remaining = self._compute_time_remaining(attempt, duration_minutes)

        responses = await attempt_repository.get_all_responses(db, attempt_id)
        response_items = [
            ResponseStateItem(
                question_no=r.question_no,
                question_id=r.question_id,
                selected_option=r.selected_option,
                selected_options=r.selected_options,
                is_marked_review=r.is_marked_review,
                visit_count=r.visit_count,
            )
            for r in responses
        ]

        return AttemptStateResponse(
            attempt_id=attempt.id,
            exam_id=attempt.exam_id,
            attempt_number=attempt.attempt_number,
            status=current_status,
            started_at=attempt.started_at,
            time_remaining_seconds=max(0, time_remaining),
            responses=response_items,
        )

    # ── Submit exam ───────────────────────────────────────────────────────────

    async def submit_exam(
        self,
        db: AsyncSession,
        attempt_id: UUID,
        student_id: UUID,
    ) -> AttemptResultResponse:
        """
        Submit exam. Computes scores and stores as JSONB (ADR-006).

        Steps:
          1. Load attempt, validate ownership + ongoing status
          2. Check timer (30-second grace period per ADR-005)
          3. Load all responses
          4. Load all questions WITH correct_option (server-side ONLY)
          5. Compute scores via _compute_result_stub() (replaced Day 9)
          6. Transition attempt to 'submitted' via state_machine
          7. Store all score JSONB + set status atomically via repository
          8. Return AttemptResultResponse (NO correct_option in output)

        Raises:
          NotFound if attempt not found
          Forbidden if not owned by this student or not ongoing
          BadRequest if timer expired (beyond 30s grace)
        """
        # Use SELECT FOR UPDATE to prevent concurrent double-submit
        locked_attempt = await attempt_repository.get_attempt_for_submit(db, attempt_id)
        if locked_attempt is None:
            # Either not found, or another request holds the lock right now
            existing = await attempt_repository.get_attempt_by_id(db, attempt_id)
            if existing is None:
                raise NotFound(f"Attempt {attempt_id} not found")
            raise Conflict("This attempt is currently being submitted. Please wait a moment.")

        attempt = locked_attempt
        # Re-run ownership check on the locked row
        if attempt.child_profile_id:
            from app.modules.user.child_repository import child_repository as child_repo
            is_owner = await child_repo.validate_ownership(
                attempt.child_profile_id, student_id, db
            )
            if not is_owner:
                raise Forbidden("This attempt does not belong to your child")
        elif attempt.student_id != student_id:
            raise Forbidden("This attempt does not belong to you")

        self._assert_ongoing(attempt)

        # Timer check with 30-second grace
        try:
            exam = await catalog_service.get_exam(db, attempt.exam_id)
            duration_minutes = exam.duration_minutes
        except Exception:
            duration_minutes = 90

        remaining = self._compute_time_remaining(attempt, duration_minutes)
        if remaining < -30:   # 30-second grace period
            raise BadRequest(
                "Cannot submit: exam time has expired. "
                f"Timer expired {abs(remaining)} seconds ago."
            )

        # Score computation via Analysis module
        from app.modules.analysis.service import analysis_service
        result_data = await analysis_service.generate_report(attempt_id, db)

        # Transition state (sets submitted_at + duration_seconds)
        attempt = await transition(attempt, "submitted", db)

        # Merge transition fields with score data
        result_data["status"] = "submitted"

        # Persist scores atomically
        await attempt_repository.update_attempt_result(db, attempt_id, result_data)

        # Reload to get final persisted state
        final = await attempt_repository.get_attempt_by_id(db, attempt_id)

        return AttemptResultResponse(
            attempt_id=final.id,
            exam_id=final.exam_id,
            status=str(final.status.value if hasattr(final.status, "value") else final.status),
            attempt_number=final.attempt_number,
            submitted_at=final.submitted_at,
            total_score=final.total_score or 0,
            total_correct=final.total_correct or 0,
            total_wrong=final.total_wrong or 0,
            total_skipped=final.total_skipped or 0,
            percentage=float(final.percentage or 0.0),
            grade=final.grade or "Below Average",
            section_scores=final.section_scores or [],
            topic_scores=final.topic_scores or [],
            time_analysis=final.time_analysis or {},
            recommendations=final.recommendations or [],
        )

    # ── List student attempts ─────────────────────────────────────────────────

    async def get_student_attempts(
        self,
        db: AsyncSession,
        student_id: UUID,
        exam_id: int,
    ) -> list[AttemptSummary]:
        """Return all attempts by this student for a given exam, newest first."""
        attempts = await attempt_repository.get_student_attempts(db, student_id, exam_id)
        return [
            AttemptSummary(
                attempt_id=a.id,
                exam_id=a.exam_id,
                attempt_number=a.attempt_number,
                status=str(a.status.value if hasattr(a.status, "value") else a.status),
                total_score=a.total_score,
                total_correct=a.total_correct,
                total_wrong=a.total_wrong,
                total_skipped=a.total_skipped,
                percentage=float(a.percentage) if a.percentage is not None else None,
                grade=a.grade,
                started_at=a.started_at,
                submitted_at=a.submitted_at,
            )
            for a in attempts
        ]

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get_owned_attempt(self, db, attempt_id, parent_id):
        """Load attempt and verify it belongs to this parent's child (or the student directly)."""
        attempt = await attempt_repository.get_attempt_by_id(db, attempt_id)
        if attempt is None:
            raise NotFound(f"Attempt {attempt_id} not found")
        if attempt.child_profile_id:
            from app.modules.user.child_repository import child_repository as child_repo
            is_owner = await child_repo.validate_ownership(
                attempt.child_profile_id, parent_id, db
            )
            if not is_owner:
                raise Forbidden("This attempt does not belong to your child")
        elif attempt.student_id != parent_id:
            raise Forbidden("This attempt does not belong to you")
        return attempt

    def _assert_ongoing(self, attempt) -> None:
        """Raise Forbidden if attempt is not in 'ongoing' status."""
        current = str(attempt.status.value if hasattr(attempt.status, "value") else attempt.status)
        if current == "submitted":
            raise AttemptAlreadySubmittedException()
        if current != "ongoing":
            raise Forbidden(
                f"Attempt is '{current}' — only ongoing attempts can be modified."
            )

    def _compute_time_remaining(self, attempt, duration_minutes: int) -> int:
        """Return seconds remaining on exam timer. Negative means expired."""
        now = datetime.now(timezone.utc)
        started = attempt.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        elapsed = int((now - started).total_seconds())
        return (duration_minutes * 60) - elapsed

    async def _assert_timer_valid(self, db, attempt) -> None:
        """Check exam timer. Raises BadRequest if strictly expired."""
        try:
            exam = await catalog_service.get_exam(db, attempt.exam_id)
            duration = exam.duration_minutes
        except Exception:
            duration = 90
        remaining = self._compute_time_remaining(attempt, duration)
        if remaining < 0:
            raise BadRequest("Exam timer has expired. Your attempt has been saved.")

    async def _get_question_no(self, db, question_id: int) -> int:
        """Fetch question_no for a question_id (needed for response row)."""
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT question_no FROM questions WHERE id = :qid"),
            {"qid": question_id},
        )
        row = result.fetchone()
        if row is None:
            raise NotFound(f"Question {question_id} not found")
        return row[0]

    async def _load_questions_with_answers(self, db, exam_id: int) -> list:
        """
        Load questions WITH correct_option for server-side scoring.
        This data NEVER leaves this function — it flows to _compute_result_stub()
        and the results are stored as aggregate JSONB, not raw correct_option values.
        """
        from sqlalchemy import text
        result = await db.execute(
            text(
                "SELECT id, question_no, correct_option, section_id, topic_id, marks "
                "FROM questions WHERE exam_id = :exam_id ORDER BY question_no"
            ),
            {"exam_id": exam_id},
        )
        rows = result.fetchall()
        return [
            {
                "id": r[0],
                "question_no": r[1],
                "correct_option": r[2],
                "section_id": r[3],
                "topic_id": r[4],
                "marks": r[5],
            }
            for r in rows
        ]

    async def _validate_assignment(
        self, db, assignment_id: int, student_id: UUID
    ) -> None:
        """Validate exam assignment: exists, belongs to student, not exhausted."""
        from sqlalchemy import text
        result = await db.execute(
            text(
                "SELECT is_active, max_attempts, attempts_used, valid_until "
                "FROM exam_assignments WHERE id = :aid AND student_id = :sid"
            ),
            {"aid": assignment_id, "sid": str(student_id)},
        )
        row = result.fetchone()
        if row is None:
            raise NotFound(f"Assignment {assignment_id} not found for this student")
        is_active, max_attempts, attempts_used, valid_until = row
        if not is_active:
            raise Forbidden("This assignment is no longer active")
        if attempts_used >= max_attempts:
            raise Forbidden(
                f"Maximum attempts reached ({attempts_used}/{max_attempts})"
            )
        if valid_until and valid_until < datetime.now(timezone.utc):
            raise Forbidden("This assignment has expired")





# Module-level singleton — import this in router.py
attempt_service = AttemptService()
