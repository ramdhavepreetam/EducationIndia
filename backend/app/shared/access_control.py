"""
Shared access-control utility — ADR-014.

Single source of truth for free-vs-paid tier decisions.
Every module imports gate functions from here.

Usage in a service:
    ctx = await get_access_context(parent_id, db)
    allowed, reason = await can_start_exam(ctx, exam_id, child_id, db)
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class AccessContext:
    parent_id: UUID
    is_paid: bool
    free_exam_id: int
    free_max_attempts: int


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
    if ctx.is_paid:
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


def can_see_full_analysis(ctx: AccessContext) -> bool:
    return ctx.is_paid


def can_download_pdf(ctx: AccessContext) -> bool:
    return ctx.is_paid


def get_tier(ctx: AccessContext) -> str:
    return "paid" if ctx.is_paid else "free"
