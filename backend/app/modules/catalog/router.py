"""
Catalog module router — HTTP layer only.

Routers call services. No business logic or DB queries here.
Endpoints:
  GET  /api/catalog/boards              → list active boards (public)
  GET  /api/catalog/exams               → list exams with filters (public)
  GET  /api/catalog/exams/{id}          → single exam with sections + topics (public)
  PUT  /api/catalog/exams/{id}/publish  → admin only, sets is_active=True
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.modules.auth.dependencies import UserIdentity, require_admin, verify_token
from app.modules.catalog.schemas import (
    BoardResponse,
    ExamAccessResponse,
    ExamDetailResponse,
    ExamSummaryResponse,
    PublishExamResponse,
)
from app.modules.catalog.service import catalog_service

router = APIRouter()


@router.get("/boards", response_model=list[BoardResponse])
async def list_boards(db: AsyncSession = Depends(get_db)):
    """
    List all active exam boards.
    Public — no authentication required.
    Example: [{ "short_code": "MSCE", "name_en": "Maharashtra State Council..." }]
    """
    boards = await catalog_service.list_boards(db)
    return boards


@router.get("/exams", response_model=list[ExamSummaryResponse])
async def list_exams(
    board_id: Optional[int] = Query(None, description="Filter by board ID"),
    std_class: Optional[int] = Query(None, description="Filter by standard (5 or 8)"),
    year: Optional[int] = Query(None, description="Filter by exam year"),
    db: AsyncSession = Depends(get_db),
):
    """
    List available exams with optional filters.
    Public — no authentication required.
    Students only see active exams (is_active=True).
    """
    exams = await catalog_service.list_exams(
        db,
        board_id=board_id,
        std_class=std_class,
        year=year,
        is_admin=False,
    )
    return exams


@router.get("/exams/accessible", response_model=list[ExamAccessResponse])
async def list_exams_accessible(
    board_id: Optional[int] = Query(None, description="Filter by board ID"),
    std_class: Optional[int] = Query(None, description="Filter by standard (5 or 8)"),
    year: Optional[int] = Query(None, description="Filter by exam year"),
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """
    List exams with access flags for the authenticated parent (ADR-014).
    Exams the parent cannot access have is_accessible=false + lock_reason.
    """
    return await catalog_service.list_exams_with_access(
        db,
        identity.id,
        board_id=board_id,
        std_class=std_class,
        year=year,
    )


@router.get("/exams/{exam_id}", response_model=ExamDetailResponse)
async def get_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single exam with all sections and topics.
    Public — no authentication required.
    Returns 404 if exam does not exist or is not active.
    """
    exam = await catalog_service.get_active_exam(db, exam_id)
    return exam


@router.put("/exams/{exam_id}/publish", response_model=PublishExamResponse)
async def publish_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    _: UserIdentity = Depends(require_admin),
):
    """
    Publish an exam — sets is_active=True, making it visible to students.
    Admin only (exam_admin or super_admin role required).
    Returns 404 if exam_id does not exist.
    Returns 403 if caller is not an admin.
    """
    exam = await catalog_service.publish_exam(db, exam_id)
    return PublishExamResponse(
        id=exam.id,
        is_active=exam.is_active,
        message=f"Exam '{exam.title_en}' is now published and visible to students.",
    )
