"""
Admin/Orchestrator router.
ZERO business logic here — delegates to other module services/repos.
All admin endpoints require exam_admin or super_admin role.

Routes:
  GET  /api/admin/dashboard/student         → student dashboard (Day 11)
  GET  /api/admin/dashboard/overview        → aggregate stats for admin panel
  GET  /api/admin/dashboard/attempts/recent → last 20 attempts across all students
  GET  /api/admin/questions/stats           → question_stats table with question_no
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from uuid import UUID

from app.database import get_db
from app.modules.auth.dependencies import require_student, require_admin, UserIdentity
from app.modules.catalog.service import catalog_service
from app.modules.attempt.repository import attempt_repository
from app.modules.catalog.schemas import ExamSummaryResponse, PublishExamResponse
from app.modules.admin.schemas import (
    StudentDashboardResponse,
    StudentDashboardStats,
    AdminOverviewStats,
    AdminAttemptRow,
    QuestionStatRow,
    AdminExamRow,
)

router = APIRouter()


# ── Student dashboard (Day 11) ────────────────────────────────────────────────

@router.get("/dashboard/student", response_model=StudentDashboardResponse)
async def get_student_dashboard(
    current_user: UserIdentity = Depends(require_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the student dashboard data (orchestrator pattern).
    Aggregates active exams from Catalog and all attempts from Attempt module.
    """
    exams = await catalog_service.list_exams(db, is_admin=False)

    attempts_orm = await attempt_repository.get_all_student_attempts(db, current_user.id)

    # status is a SQLAlchemy enum — extract its string value for comparison
    def _status(a) -> str:
        return str(a.status.value if hasattr(a.status, "value") else a.status)

    submitted_attempts = [
        a for a in attempts_orm
        if _status(a) == "submitted" and a.percentage is not None
    ]

    total_attempts = len(attempts_orm)
    exams_completed = len(set(a.exam_id for a in submitted_attempts))
    best_score = max(
        (a.total_score for a in submitted_attempts if a.total_score is not None),
        default=0,
    )
    avg_percentage = 0.0
    if submitted_attempts:
        avg_percentage = sum(float(a.percentage) for a in submitted_attempts) / len(submitted_attempts)

    stats = StudentDashboardStats(
        total_attempts=total_attempts,
        avg_percentage=round(avg_percentage, 1),
        best_score=best_score,
        exams_completed=exams_completed,
    )

    # Map ORM Attempt objects → AttemptSummary (ORM has `id`; schema expects `attempt_id`)
    recent = [
        AttemptSummary(
            attempt_id=a.id,
            exam_id=a.exam_id,
            attempt_number=a.attempt_number,
            status=_status(a),
            total_score=a.total_score,
            total_correct=a.total_correct,
            total_wrong=a.total_wrong,
            total_skipped=a.total_skipped,
            percentage=float(a.percentage) if a.percentage is not None else None,
            grade=a.grade,
            started_at=a.started_at,
            submitted_at=a.submitted_at,
        )
        for a in attempts_orm[:5]
    ]

    return StudentDashboardResponse(
        available_exams=exams,
        recent_attempts=recent,
        stats=stats,
    )


# ── Admin panel endpoints ─────────────────────────────────────────────────────

@router.get("/dashboard/overview", response_model=AdminOverviewStats)
async def get_admin_overview(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Aggregate stats for admin dashboard cards.
    Counts: students, total attempts, active exams, total questions.
    All queries are simple COUNTs — no business logic.
    """
    row = (
        await db.execute(
            text("""
                SELECT
                  (SELECT COUNT(*) FROM user_profiles WHERE role = 'student') AS total_students,
                  (SELECT COUNT(*) FROM attempts)                              AS total_attempts,
                  (SELECT COUNT(*) FROM exams WHERE is_active = true)          AS active_exams,
                  (SELECT COUNT(*) FROM questions)                             AS total_questions
            """)
        )
    ).mappings().first()

    return AdminOverviewStats(
        total_students=int(row["total_students"]),
        total_attempts=int(row["total_attempts"]),
        active_exams=int(row["active_exams"]),
        total_questions=int(row["total_questions"]),
    )


@router.get("/dashboard/attempts/recent", response_model=List[AdminAttemptRow])
async def get_recent_attempts_all_students(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Last 20 attempts across all students for the admin recent activity table.
    Joins attempts + user_profiles (name) + exams (title).
    """
    rows = (
        await db.execute(
            text("""
                SELECT
                    a.id            AS attempt_id,
                    a.student_id,
                    up.full_name    AS student_name,
                    a.exam_id,
                    e.title_en      AS exam_title,
                    a.status,
                    a.total_score,
                    a.percentage,
                    a.grade,
                    a.started_at,
                    a.submitted_at
                FROM attempts a
                LEFT JOIN user_profiles up ON up.id = a.student_id
                LEFT JOIN exams e          ON e.id  = a.exam_id
                ORDER BY a.started_at DESC
                LIMIT 20
            """)
        )
    ).mappings().all()

    return [AdminAttemptRow(**dict(r)) for r in rows]


@router.get("/catalog/exams", response_model=List[AdminExamRow])
async def list_all_exams_admin(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    List ALL exams (active + inactive) with question counts for ExamPublisherPage.
    Delegates to catalog + a raw count query.
    """
    rows = (
        await db.execute(
            text("""
                SELECT
                    e.id, e.paper_code, e.set_code,
                    e.title_en, e.title_mr,
                    e.is_active, e.total_questions,
                    ev.title_en AS event_title,
                    ev.year     AS event_year,
                    COUNT(q.id) AS question_count
                FROM exams e
                LEFT JOIN exam_events ev ON ev.id = e.event_id
                LEFT JOIN questions q    ON q.exam_id = e.id
                GROUP BY e.id, ev.id
                ORDER BY e.id
            """)
        )
    ).mappings().all()

    return [AdminExamRow(**dict(r)) for r in rows]


@router.put("/catalog/exams/{exam_id}/publish", response_model=PublishExamResponse)
async def admin_publish_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Publish exam — sets is_active=True. Admin only."""
    exam = await catalog_service.publish_exam(db, exam_id)
    return PublishExamResponse(
        id=exam.id,
        is_active=exam.is_active,
        message=f"Exam '{exam.title_en}' is now published.",
    )


@router.put("/catalog/exams/{exam_id}/unpublish", response_model=PublishExamResponse)
async def admin_unpublish_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Unpublish exam — sets is_active=False. Admin only."""
    exam = await catalog_service.unpublish_exam(db, exam_id)
    return PublishExamResponse(
        id=exam.id,
        is_active=exam.is_active,
        message=f"Exam '{exam.title_en}' is now unpublished.",
    )


@router.get("/questions/stats", response_model=List[QuestionStatRow])
async def get_question_stats(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Question stats for a given exam — for the admin Stats page.
    Joins question_stats + questions.question_no.
    Sorted by question_no ascending.
    """
    rows = (
        await db.execute(
            text("""
                SELECT
                    qs.question_id,
                    q.question_no,
                    qs.total_attempts,
                    qs.correct_count,
                    qs.wrong_count,
                    qs.skip_count,
                    ROUND(qs.avg_time_seconds::numeric, 1) AS avg_time_seconds,
                    ROUND(qs.actual_difficulty::numeric, 3) AS actual_difficulty,
                    CASE
                        WHEN qs.total_attempts > 0
                        THEN ROUND(qs.correct_count::numeric / qs.total_attempts * 100, 1)
                        ELSE NULL
                    END AS correct_pct
                FROM question_stats qs
                JOIN questions q ON q.id = qs.question_id
                WHERE q.exam_id = :exam_id
                ORDER BY q.question_no
            """),
            {"exam_id": exam_id},
        )
    ).mappings().all()

    return [QuestionStatRow(**dict(r)) for r in rows]


# ── Admin settings & subscription endpoints (ADR-014) ─────────────────────────

@router.get("/settings")
async def get_all_settings(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Returns all app_settings rows. Admin only."""
    from app.modules.payment.repository import payment_repository
    return await payment_repository.get_all_settings(db)


@router.put("/settings/{key}")
async def update_setting(
    key: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    admin: UserIdentity = Depends(require_admin),
):
    """
    Updates one app_settings row. Admin only.
    If key=payment_amount_inr, also syncs subscription_plans.price_inr.
    """
    from app.modules.payment.repository import payment_repository
    value = body.get("value")
    if value is None:
        from app.shared.exceptions import BadRequest
        raise BadRequest("'value' field is required")

    await payment_repository.update_setting(db, key, str(value), admin.id)

    # Sync plan price when amount changes
    if key == "payment_amount_inr":
        try:
            await payment_repository.sync_plan_price(db, int(value))
        except (ValueError, TypeError):
            pass

    return {"key": key, "value": str(value), "status": "updated"}


@router.get("/subscriptions")
async def list_subscriptions(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """All subscriptions with parent info. Admin only."""
    from app.modules.payment.repository import payment_repository
    return await payment_repository.get_all_subscriptions_admin(db)


@router.post("/subscriptions/{sub_id}/extend")
async def extend_subscription(
    sub_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Extends a subscription's expires_at. Admin only."""
    from app.modules.payment.repository import payment_repository
    months = body.get("months", 0)
    if not months or months < 1:
        from app.shared.exceptions import BadRequest
        raise BadRequest("'months' must be >= 1")

    result = await payment_repository.extend_subscription(db, sub_id, months)
    return {"status": "extended", "expires_at": str(result.get("expires_at"))}

@router.post("/subscriptions/{sub_id}/cancel")
async def cancel_subscription(
    sub_id: str,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Cancels a subscription. Admin only."""
    from app.modules.payment.repository import payment_repository
    result = await payment_repository.cancel_subscription(db, sub_id)
    return {"status": "cancelled", "id": str(result.get("id"))}


@router.post("/subscriptions/grant")
async def grant_subscription(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Admin manually grants a subscription to a parent by email.
    Body: { email: str, plan_id: int, months: int }
    """
    from app.modules.payment.repository import payment_repository
    from app.shared.exceptions import BadRequest, NotFound

    email = body.get("email", "").strip().lower()
    plan_id = body.get("plan_id")
    months = body.get("months", 5)

    if not email:
        raise BadRequest("'email' is required")
    if not plan_id:
        raise BadRequest("'plan_id' is required")

    # Find parent by email
    parent = await payment_repository.find_parent_by_email(db, email)
    if not parent:
        raise NotFound(f"No parent account found for '{email}'")

    # Create the subscription
    result = await payment_repository.grant_subscription(
        db, str(parent["id"]), plan_id, months
    )

    return {
        "status": "granted",
        "subscription_id": str(result.get("id")),
        "parent_name": parent.get("full_name"),
        "parent_email": email,
        "expires_at": str(result.get("expires_at")),
    }
