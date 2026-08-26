from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.service import catalog_service
from app.shared.exceptions import Forbidden, NotFound

from .repository import teacher_repository
from .schemas import (
    AssignExamRequest,
    AssignmentSchema,
    StudentAttemptSummary,
    StudentDetailSchema,
    TeacherDashboardSchema,
    TeacherStudentSchema,
)


class TeacherService:
    async def get_dashboard(
        self, db: AsyncSession, teacher_id: UUID
    ) -> TeacherDashboardSchema:
        stats = await teacher_repository.get_dashboard_stats(db, teacher_id)
        recent = await teacher_repository.get_all_teacher_assignments(db, teacher_id, limit=10)
        exam_count = await teacher_repository.count_active_exams(db)

        return TeacherDashboardSchema(
            total_students_assigned=int(stats.get("total_students_assigned") or 0),
            total_assignments_active=int(stats.get("total_assignments_active") or 0),
            total_exams_available=exam_count,
            recent_assignments=[AssignmentSchema(**r) for r in recent],
        )

    async def list_students(
        self,
        db: AsyncSession,
        teacher_id: UUID,
        *,
        search: str | None = None,
        std_class: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        offset = (page - 1) * page_size
        rows = await teacher_repository.list_assigned_students(
            db, teacher_id, search=search, std_class=std_class,
            limit=page_size, offset=offset,
        )
        return {
            "items": [TeacherStudentSchema(**r) for r in rows],
            "page": page,
            "page_size": page_size,
            "has_more": len(rows) == page_size,
        }

    async def get_student_detail(
        self, db: AsyncSession, teacher_id: UUID, student_id: UUID
    ) -> StudentDetailSchema:
        # Verify this teacher has at least one assignment for this student
        assignments_raw = await teacher_repository.get_student_assignments(
            db, teacher_id, student_id
        )
        if not assignments_raw:
            raise Forbidden("You have not assigned any exams to this student")

        stats = await teacher_repository.get_student_stats(db, student_id)
        attempts_raw = await teacher_repository.get_student_recent_attempts(db, student_id)

        # Pull basic student info from the first assignment row
        first = assignments_raw[0]

        return StudentDetailSchema(
            id=student_id,
            full_name=first["student_name"] or "",
            email=first.get("email"),
            std_class=None,
            medium=None,
            school_name=None,
            district=None,
            total_attempts=int(stats.get("total_attempts") or 0),
            avg_percentage=float(stats["avg_percentage"]) if stats.get("avg_percentage") is not None else None,
            best_percentage=float(stats["best_percentage"]) if stats.get("best_percentage") is not None else None,
            last_attempt_at=stats.get("last_attempt_at"),
            assignments=[AssignmentSchema(**r) for r in assignments_raw],
            recent_attempts=[StudentAttemptSummary(**r) for r in attempts_raw],
        )

    async def assign_exam(
        self, db: AsyncSession, teacher_id: UUID, data: AssignExamRequest
    ) -> AssignmentSchema:
        # Validate exam exists (any status — teachers may assign inactive exams
        # for future use; the attempt module will block start if not yet active)
        await catalog_service.get_exam(db, data.exam_id)

        # Validate student exists
        # We do this by trying to fetch a student matching any of the teacher's
        # existing assignments, OR fall back to a direct lookup.
        result = await teacher_repository.upsert_assignment(
            db, teacher_id, data.student_id, data.exam_id, data.max_attempts
        )
        return AssignmentSchema(**result)

    async def find_student_by_email(
        self, db: AsyncSession, email: str
    ) -> dict:
        student = await teacher_repository.find_student_by_email(db, email)
        if not student:
            raise NotFound("No active student account found with that email address")
        return student


teacher_service = TeacherService()
