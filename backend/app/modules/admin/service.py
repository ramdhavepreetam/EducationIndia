from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.repository import admin_repository
from app.modules.admin.schemas import (
    AdminAttemptRow,
    AdminExamRow,
    AdminOverviewStats,
    QuestionStatRow,
    StudentDashboardResponse,
    StudentDashboardStats,
    UpdateExamAdminRequest,
)
from app.modules.attempt.repository import attempt_repository
from app.modules.attempt.schemas import AttemptSummary
from app.modules.auth.dependencies import UserIdentity
from app.modules.catalog.service import catalog_service
from app.shared.exceptions import Forbidden


class AdminService:
    async def get_student_dashboard(
        self,
        db: AsyncSession,
        current_user: UserIdentity,
        child_id: UUID | None = None,
    ) -> StudentDashboardResponse:
        target_id = current_user.id
        if current_user.role == "parent":
            if not child_id:
                target_id = None
            else:
                from app.modules.user.child_repository import ChildRepository

                child_repo = ChildRepository()
                child = await child_repo.get_by_id(child_id, current_user.id, db)
                if not child:
                    raise Forbidden("Not authorized to view this child's dashboard")
                target_id = child_id

        exams = await catalog_service.list_exams(db, is_admin=False)
        stats = StudentDashboardStats(
            total_attempts=0,
            avg_percentage=0.0,
            best_score=0,
            exams_completed=0,
        )
        recent: list[AttemptSummary] = []

        if target_id is not None:
            agg_row = await admin_repository.get_student_dashboard_stats(db, target_id)
            stats = StudentDashboardStats(
                total_attempts=int(agg_row.get("total_attempts") or 0),
                exams_completed=int(agg_row.get("exams_completed") or 0),
                best_score=int(agg_row.get("best_score") or 0),
                avg_percentage=round(float(agg_row.get("avg_percentage") or 0), 1),
            )

            recent_orm = await attempt_repository.get_all_student_attempts(
                db, target_id, limit=5
            )

            recent = [
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
                for a in recent_orm
            ]

        return StudentDashboardResponse(
            available_exams=exams,
            recent_attempts=recent,
            stats=stats,
        )

    async def get_overview(self, db: AsyncSession) -> AdminOverviewStats:
        row = await admin_repository.get_overview_stats(db)
        return AdminOverviewStats(
            total_students=int(row.get("total_students") or 0),
            total_attempts=int(row.get("total_attempts") or 0),
            active_exams=int(row.get("active_exams") or 0),
            total_questions=int(row.get("total_questions") or 0),
        )

    async def get_recent_attempts(self, db: AsyncSession) -> list[AdminAttemptRow]:
        rows = await admin_repository.get_recent_attempts(db)
        return [AdminAttemptRow(**row) for row in rows]

    async def list_exams_admin(self, db: AsyncSession) -> list[AdminExamRow]:
        rows = await admin_repository.list_exams_admin(db)
        return [AdminExamRow(**row) for row in rows]

    async def update_exam_admin(
        self, db: AsyncSession, exam_id: int, data: UpdateExamAdminRequest
    ) -> AdminExamRow:
        from app.shared.exceptions import NotFound

        values = data.model_dump(exclude_unset=True)
        row = await admin_repository.update_exam_admin(db, exam_id, values)
        if not row:
            raise NotFound(f"Exam {exam_id} not found")
        return AdminExamRow(**row)

    async def get_question_stats(
        self, db: AsyncSession, exam_id: int
    ) -> list[QuestionStatRow]:
        rows = await admin_repository.get_question_stats(db, exam_id)
        return [QuestionStatRow(**row) for row in rows]


admin_service = AdminService()
