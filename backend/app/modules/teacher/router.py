from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.dependencies import UserIdentity, require_teacher

from .schemas import (
    AssignExamRequest,
    AssignmentSchema,
    StudentDetailSchema,
    TeacherDashboardSchema,
)
from .service import teacher_service

router = APIRouter(tags=["teacher"])


@router.get("/dashboard", response_model=TeacherDashboardSchema)
async def get_dashboard(
    identity: UserIdentity = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    return await teacher_service.get_dashboard(db, identity.id)


@router.get("/students")
async def list_students(
    search: Optional[str] = Query(None, description="Search by name or email"),
    std_class: Optional[int] = Query(None, ge=5, le=8),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    identity: UserIdentity = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    return await teacher_service.list_students(
        db, identity.id,
        search=search, std_class=std_class,
        page=page, page_size=page_size,
    )


@router.get("/students/lookup")
async def lookup_student_by_email(
    email: str = Query(..., description="Student's registered email address"),
    identity: UserIdentity = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Find a student account by email before assigning an exam."""
    return await teacher_service.find_student_by_email(db, email)


@router.get("/students/{student_id}", response_model=StudentDetailSchema)
async def get_student_detail(
    student_id: UUID,
    identity: UserIdentity = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    return await teacher_service.get_student_detail(db, identity.id, student_id)


@router.post("/assign", response_model=AssignmentSchema, status_code=201)
async def assign_exam(
    data: AssignExamRequest,
    identity: UserIdentity = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    return await teacher_service.assign_exam(db, identity.id, data)
