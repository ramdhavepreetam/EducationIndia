"""
Shared access-control utility — ADR-014.

Single source of truth for free-vs-paid tier decisions.
Every module imports gate functions from here.

Usage in a service:
    ctx = await get_access_context(parent_id, db)
    allowed, reason = await can_start_exam(ctx, exam_id, child_id, db)
"""

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class AccessContext:
    parent_id: UUID
    is_paid: bool
    free_exam_id: int
    free_max_attempts: int
    entitled_exam_ids: set[int] = field(default_factory=set)


async def get_access_context(
    parent_id: UUID, db: AsyncSession
) -> AccessContext:
    """
    Single DB query.  Call ONCE per request.
    Reads subscription status + app_settings together.
    """
    result = await db.execute(
        text("""
            SELECT
                parent_has_active_subscription(:p_parent_id) AS is_paid,
                (SELECT value::int FROM app_settings
                 WHERE key = 'free_tier_exam_id')      AS free_exam_id,
                (SELECT value::int FROM app_settings
                 WHERE key = 'free_tier_max_attempts')  AS free_max_attempts
        """),
        {"p_parent_id": str(parent_id)},
    )
    row = result.mappings().first()
    return AccessContext(
        parent_id=parent_id,
        is_paid=row["is_paid"],
        free_exam_id=row["free_exam_id"],
        free_max_attempts=row["free_max_attempts"],
    )


async def get_accessible_exam_ids(
    parent_id: UUID,
    exam_ids: list[int],
    db: AsyncSession,
) -> set[int]:
    """Return exam IDs covered by any active subscription for this parent."""
    if not exam_ids:
        return set()
    result = await db.execute(
        text("""
            SELECT DISTINCT e.id
            FROM exams e
            JOIN exam_events ev ON ev.id = e.event_id
            JOIN subscription_plan_entitlements spe ON (
                spe.scope_type = 'all'
                OR (spe.scope_type = 'board' AND spe.board_id = ev.board_id)
                OR (spe.scope_type = 'category' AND spe.category_id = ev.category_id)
                OR (spe.scope_type = 'std_class' AND spe.std_class = ev.std_class)
                OR (spe.scope_type = 'event' AND spe.event_id = ev.id)
                OR (spe.scope_type = 'exam' AND spe.exam_id = e.id)
            )
            JOIN subscriptions s ON s.plan_id = spe.plan_id
            WHERE s.parent_id = :parent_id
              AND s.status = 'active'
              AND s.expires_at > now()
              AND e.id = ANY(:exam_ids)
        """),
        {"parent_id": str(parent_id), "exam_ids": exam_ids},
    )
    return {int(row[0]) for row in result.all()}


async def has_exam_entitlement(
    parent_id: UUID,
    exam_id: int,
    db: AsyncSession,
) -> bool:
    return exam_id in await get_accessible_exam_ids(parent_id, [exam_id], db)


async def can_start_exam(
    ctx: AccessContext,
    exam_id: int,
    child_profile_id: UUID,
    db: AsyncSession,
) -> tuple[bool, str]:
    """
    Returns (allowed, reason).
    reason is used by the frontend to show the correct UpgradePrompt.
    """
    if exam_id in ctx.entitled_exam_ids:
        return True, ""

    if ctx.is_paid and await has_exam_entitlement(ctx.parent_id, exam_id, db):
        return True, ""

    if exam_id != ctx.free_exam_id:
        return False, "upgrade_required_exam"

    # Count completed attempts for this learner on this exam.
    # Direct-student attempts use student_id; parent-created child attempts use child_profile_id.
    result = await db.execute(
        text("""
            SELECT COUNT(*) FROM attempts
            WHERE (child_profile_id = :cid OR student_id = :cid)
              AND exam_id = :eid
              AND status IN ('submitted', 'expired')
        """),
        {"cid": str(child_profile_id), "eid": exam_id},
    )
    count = result.scalar()
    if count >= ctx.free_max_attempts:
        return False, "upgrade_required_attempts"

    return True, ""


async def can_see_full_analysis(ctx: AccessContext, exam_id: int, db: AsyncSession) -> bool:
    if exam_id in ctx.entitled_exam_ids:
        return True
    return ctx.is_paid and await has_exam_entitlement(ctx.parent_id, exam_id, db)


async def can_download_pdf(ctx: AccessContext, exam_id: int, db: AsyncSession) -> bool:
    return await can_see_full_analysis(ctx, exam_id, db)


def get_tier(ctx: AccessContext) -> str:
    return "paid" if ctx.is_paid else "free"
