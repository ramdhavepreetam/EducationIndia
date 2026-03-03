"""
Parent monitoring router — all /api/parent/* endpoints.

ZERO business logic here. Delegates to parent_service exclusively.
Every endpoint requires the 'parent' role (require_parent dependency).

Routes:
  GET    /api/parent/dashboard                           → ParentDashboardSchema
  GET    /api/parent/children                            → list[ChildProfileSchema]
  GET    /api/parent/children/{student_id}               → ChildDetailSchema
  GET    /api/parent/children/{student_id}/attempts      → paginated dict
  GET    /api/parent/children/{student_id}/topics        → list[WeakTopicSchema]
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.dependencies import UserIdentity, require_parent
from app.modules.user.parent_schemas import (
    ChildDetailSchema,
    ChildProfileSchema,
    ParentDashboardSchema,
    WeakTopicSchema,
)
from app.modules.user.parent_service import parent_service

router = APIRouter(tags=["parent"])


@router.get("/dashboard", response_model=ParentDashboardSchema)
async def get_dashboard(
    current_user: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    """Returns all linked children + full detail for the first child."""
    return await parent_service.get_dashboard(db, current_user.id)


@router.get("/children", response_model=list[ChildProfileSchema])
async def get_children(
    current_user: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    """List all children linked to this parent."""
    return await parent_service.get_children(db, current_user.id)





@router.get("/children/{student_id}", response_model=ChildDetailSchema)
async def get_child_detail(
    student_id: UUID,
    current_user: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    """Full detail for one linked child: profile + stats + attempts + topics."""
    return await parent_service.get_child_detail(db, current_user.id, student_id)


@router.get("/children/{student_id}/attempts")
async def get_child_attempts(
    student_id: UUID,
    page: int = 1,
    size: int = 10,
    current_user: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    """Paginated attempt history for a linked child."""
    return await parent_service.get_child_attempts_paged(
        db, current_user.id, student_id, page, size
    )


@router.get("/children/{student_id}/topics", response_model=list[WeakTopicSchema])
async def get_child_topics(
    student_id: UUID,
    current_user: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db),
):
    """Per-topic performance for a linked child."""
    return await parent_service.get_child_topics(db, current_user.id, student_id)



