"""
Admin/Orchestrator router.
ZERO business logic here — delegates to other module services/repos.
All admin endpoints require exam_admin or super_admin role.

Routes:
  GET  /api/admin/dashboard/student         → student dashboard (Day 11)
  GET  /api/admin/dashboard/overview        → aggregate stats for admin panel
  GET  /api/admin/dashboard/attempts/recent → last 20 attempts across all students
  GET  /api/admin/questions/stats           → question_stats table with question_no
  POST /api/admin/catalog/events            → create new test (event + Paper I + II)
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.database import get_db
from app.modules.admin.service import admin_service
from app.modules.auth.dependencies import require_admin, require_role, UserIdentity
from app.modules.catalog.service import catalog_service
from app.modules.catalog.schemas import PublishExamResponse, EventWithExamsResponse, CreateEventRequest
from app.modules.admin.schemas import (
    StudentDashboardResponse,
    AdminOverviewStats,
    AdminAttemptRow,
    QuestionStatRow,
    AdminExamRow,
    UpdateSettingRequest,
    ExtendSubscriptionRequest,
    GrantSubscriptionRequest,
    UpdateExamAdminRequest,
)
from app.modules.payment.schemas import (
    PlanCreateRequest,
    PlanEntitlementRequest,
    PlanResponse,
    PlanUpdateRequest,
)

router = APIRouter()


# ── Student dashboard (Day 11) ────────────────────────────────────────────────

@router.get("/dashboard/student", response_model=StudentDashboardResponse)
async def get_student_dashboard(
    child_id: UUID | None = None,
    current_user: UserIdentity = Depends(require_role("student", "parent")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the student dashboard data (orchestrator pattern).
    Aggregates active exams from Catalog and all attempts from Attempt module.
    """
    return await admin_service.get_student_dashboard(db, current_user, child_id)


# ── Admin panel endpoints ─────────────────────────────────────────────────────

@router.get("/dashboard/overview", response_model=AdminOverviewStats)
async def get_admin_overview(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Aggregate stats for admin dashboard cards.
    Counts: students, total attempts, active exams, total questions.
    """
    return await admin_service.get_overview(db)


@router.get("/dashboard/attempts/recent", response_model=List[AdminAttemptRow])
async def get_recent_attempts_all_students(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Last 20 attempts across all students for the admin recent activity table.
    Joins attempts + user_profiles (name) + exams (title).
    """
    return await admin_service.get_recent_attempts(db)


@router.get("/catalog/exams", response_model=List[AdminExamRow])
async def list_all_exams_admin(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    List ALL exams (active + inactive) with question counts for ExamPublisherPage.
    """
    return await admin_service.list_exams_admin(db)


@router.patch("/catalog/exams/{exam_id}", response_model=AdminExamRow)
async def admin_update_exam(
    exam_id: int,
    data: UpdateExamAdminRequest,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Update admin-editable exam metadata, including duration_minutes."""
    return await admin_service.update_exam_admin(db, exam_id, data)


@router.put("/catalog/exams/{exam_id}/publish", response_model=PublishExamResponse)
async def admin_publish_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Publish exam — sets is_active=True. Admin only."""
    result = await catalog_service.publish_exam(db, exam_id)
    count = result.get("auto_assigned_count", 0)
    return PublishExamResponse(
        id=result["exam_id"],
        is_active=result["is_active"],
        message=f"Exam is now published. Auto-assigned to {count} student(s).",
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
    return await admin_service.get_question_stats(db, exam_id)


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
    body: UpdateSettingRequest,
    db: AsyncSession = Depends(get_db),
    admin: UserIdentity = Depends(require_admin),
):
    """
    Updates one app_settings row. Admin only.
    Plan pricing is managed through /api/admin/plans.
    """
    from app.modules.payment.repository import payment_repository
    await payment_repository.update_setting(db, key, body.value, admin.id)

    return {"key": key, "value": body.value, "status": "updated"}


@router.get("/subscriptions")
async def list_subscriptions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """All subscriptions with parent info. Admin only. Paginated."""
    from app.modules.payment.repository import payment_repository
    return await payment_repository.get_all_subscriptions_admin(db, page=page, limit=limit)


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans_admin(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """List all plans, active and inactive, with entitlement summaries."""
    from app.modules.payment.repository import payment_repository
    return await payment_repository.get_all_plans_admin(db)


@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan_admin(
    body: PlanCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Create a subscription plan and optional entitlement rows."""
    from app.modules.payment.service import payment_service
    return await payment_service.create_plan(db, body)


@router.get("/plans/scope-options")
async def get_plan_scope_options_admin(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Catalog selector options used by the plan entitlement admin UI."""
    from app.modules.payment.repository import payment_repository
    return await payment_repository.get_plan_scope_options(db)


@router.put("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan_admin(
    plan_id: int,
    body: PlanUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Update subscription plan metadata, pricing, duration, or active status."""
    from app.modules.payment.service import payment_service
    return await payment_service.update_plan(db, plan_id, body)


@router.post("/plans/{plan_id}/entitlements", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def add_plan_entitlement_admin(
    plan_id: int,
    body: PlanEntitlementRequest,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Add a catalog scope entitlement to a plan."""
    from app.modules.payment.service import payment_service
    return await payment_service.add_plan_entitlement(db, plan_id, body)


@router.delete("/plans/{plan_id}/entitlements/{entitlement_id}", response_model=PlanResponse)
async def delete_plan_entitlement_admin(
    plan_id: int,
    entitlement_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Remove a catalog scope entitlement from a plan."""
    from app.modules.payment.service import payment_service
    return await payment_service.delete_plan_entitlement(db, plan_id, entitlement_id)


@router.post("/subscriptions/{sub_id}/extend")
async def extend_subscription(
    sub_id: UUID,
    body: ExtendSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Extends a subscription's expires_at. Admin only."""
    from app.modules.payment.repository import payment_repository
    result = await payment_repository.extend_subscription(db, sub_id, body.months)
    return {"status": "extended", "expires_at": str(result.get("expires_at"))}

@router.post("/subscriptions/{sub_id}/cancel")
async def cancel_subscription(
    sub_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Cancels a subscription. Admin only."""
    from app.modules.payment.repository import payment_repository
    result = await payment_repository.cancel_subscription(db, sub_id)
    return {"status": "cancelled", "id": str(result.get("id"))}


# ── Payment analytics endpoints ───────────────────────────────────────────────

@router.get("/payments/stats")
async def get_payment_stats(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Revenue summary: totals, active count, monthly revenue. Admin only."""
    from app.modules.payment.repository import payment_repository
    return await payment_repository.get_payment_stats_admin(db)


@router.get("/payments")
async def list_all_payments(
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
    status: str | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
):
    """All payment transactions with optional filters. Admin only."""
    from app.modules.payment.repository import payment_repository
    return await payment_repository.get_all_payments_admin(
        db, status=status, search=search, page=page, limit=limit
    )


@router.get("/payments/monthly")
async def get_monthly_revenue(
    months: int = Query(default=6, ge=1, le=24, description="Number of months (1–24)"),
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """Month-by-month revenue chart data for last N months. Admin only."""
    from app.modules.payment.repository import payment_repository
    return await payment_repository.get_monthly_revenue_admin(db, months=months)


@router.get("/payments/user/{parent_id}")
async def get_payments_by_parent(
    parent_id: str,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """All payments for a specific parent. Admin drill-down."""
    from app.modules.payment.repository import payment_repository
    return await payment_repository.get_payments_by_parent_admin(db, parent_id)


@router.post("/subscriptions/grant")
async def grant_subscription(
    body: GrantSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Admin manually grants a subscription to a parent by email.
    Body: { email: str, plan_id: int, months: int }
    """
    from app.modules.payment.repository import payment_repository
    from app.shared.exceptions import NotFound

    email = body.email.lower().strip()

    # Find parent by email
    parent = await payment_repository.find_parent_by_email(db, email)
    if not parent:
        raise NotFound(f"No parent account found for '{email}'")

    # Create the subscription
    result = await payment_repository.grant_subscription(
        db, str(parent["id"]), body.plan_id, body.months
    )

    return {
        "status": "granted",
        "subscription_id": str(result.get("id")),
        "parent_name": parent.get("full_name"),
        "parent_email": email,
        "expires_at": str(result.get("expires_at")),
    }


# ── Catalog admin — create new test (event + papers) ─────────────────────────

@router.post(
    "/catalog/events",
    response_model=EventWithExamsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new test set (exam event + Paper I + Paper II)",
)
async def create_exam_event(
    data: CreateEventRequest,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Admin-only: Create a new exam event with Paper I (501) and Paper II (502).
    Sections + topics are cloned from the existing paper of the same board.
    Returns the new event with its two papers.

    Raises 400 if std_class not in (5, 8).
    Raises 409 if a paper_code + set_code collision occurs.
    """
    return await catalog_service.create_event_with_papers(db, data)
