from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TeacherRepository:
    async def list_assigned_students(
        self,
        db: AsyncSession,
        teacher_id: UUID,
        *,
        search: str | None = None,
        std_class: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        Return distinct students who have at least one active assignment made
        by this teacher. Includes aggregate stats.
        """
        where_clauses = [
            "ea.assigned_by = :teacher_id",
            "ea.is_active = true",
        ]
        params: dict = {"teacher_id": str(teacher_id), "limit": limit, "offset": offset}

        if search:
            where_clauses.append("(up.full_name ILIKE :search OR au.email ILIKE :search)")
            params["search"] = f"%{search}%"
        if std_class:
            where_clauses.append("up.std_class = :std_class")
            params["std_class"] = std_class

        where_sql = " AND ".join(where_clauses)

        rows = (await db.execute(
            text(f"""
                SELECT
                    up.id,
                    up.full_name,
                    au.email,
                    up.std_class,
                    up.medium,
                    up.school_name,
                    up.district,
                    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'submitted') AS total_attempts,
                    AVG(a.percentage) FILTER (WHERE a.status = 'submitted')    AS avg_percentage,
                    MAX(a.submitted_at) FILTER (WHERE a.status = 'submitted')  AS last_attempt_at
                FROM exam_assignments ea
                JOIN user_profiles up ON up.id = ea.student_id
                LEFT JOIN auth.users au ON au.id = ea.student_id
                LEFT JOIN attempts a ON a.student_id = ea.student_id
                WHERE {where_sql}
                GROUP BY up.id, up.full_name, au.email, up.std_class, up.medium, up.school_name, up.district
                ORDER BY up.full_name
                LIMIT :limit OFFSET :offset
            """),
            params,
        )).mappings().all()

        return [dict(r) for r in rows]

    async def get_student_assignments(
        self, db: AsyncSession, teacher_id: UUID, student_id: UUID
    ) -> list[dict]:
        rows = (await db.execute(
            text("""
                SELECT
                    ea.id,
                    ea.exam_id,
                    ea.student_id,
                    up.full_name AS student_name,
                    e.title_en   AS exam_title,
                    e.paper_code,
                    ea.max_attempts,
                    ea.attempts_used,
                    ea.is_active,
                    ea.created_at AS assigned_at
                FROM exam_assignments ea
                JOIN exams e ON e.id = ea.exam_id
                JOIN user_profiles up ON up.id = ea.student_id
                WHERE ea.assigned_by = :teacher_id
                  AND ea.student_id = :student_id
                ORDER BY ea.created_at DESC
            """),
            {"teacher_id": str(teacher_id), "student_id": str(student_id)},
        )).mappings().all()
        return [dict(r) for r in rows]

    async def get_all_teacher_assignments(
        self, db: AsyncSession, teacher_id: UUID, limit: int = 20
    ) -> list[dict]:
        rows = (await db.execute(
            text("""
                SELECT
                    ea.id,
                    ea.exam_id,
                    ea.student_id,
                    up.full_name AS student_name,
                    e.title_en   AS exam_title,
                    e.paper_code,
                    ea.max_attempts,
                    ea.attempts_used,
                    ea.is_active,
                    ea.created_at AS assigned_at
                FROM exam_assignments ea
                JOIN exams e ON e.id = ea.exam_id
                JOIN user_profiles up ON up.id = ea.student_id
                WHERE ea.assigned_by = :teacher_id
                ORDER BY ea.created_at DESC
                LIMIT :limit
            """),
            {"teacher_id": str(teacher_id), "limit": limit},
        )).mappings().all()
        return [dict(r) for r in rows]

    async def get_student_stats(
        self, db: AsyncSession, student_id: UUID
    ) -> dict:
        row = (await db.execute(
            text("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'submitted') AS total_attempts,
                    AVG(percentage) FILTER (WHERE status = 'submitted')  AS avg_percentage,
                    MAX(percentage) FILTER (WHERE status = 'submitted')  AS best_percentage,
                    MAX(submitted_at)                                     AS last_attempt_at
                FROM attempts
                WHERE student_id = :student_id
            """),
            {"student_id": str(student_id)},
        )).mappings().one_or_none()
        return dict(row) if row else {}

    async def get_student_recent_attempts(
        self, db: AsyncSession, student_id: UUID, limit: int = 10
    ) -> list[dict]:
        rows = (await db.execute(
            text("""
                SELECT
                    a.id          AS attempt_id,
                    e.title_en    AS exam_title,
                    e.paper_code,
                    a.status,
                    a.total_score,
                    a.total_correct,
                    a.total_wrong,
                    a.total_skipped,
                    a.percentage,
                    a.grade,
                    a.started_at,
                    a.submitted_at,
                    a.duration_seconds
                FROM attempts a
                JOIN exams e ON e.id = a.exam_id
                WHERE a.student_id = :student_id
                ORDER BY a.started_at DESC
                LIMIT :limit
            """),
            {"student_id": str(student_id), "limit": limit},
        )).mappings().all()
        return [dict(r) for r in rows]

    async def get_existing_assignment(
        self, db: AsyncSession, teacher_id: UUID, student_id: UUID, exam_id: int
    ) -> dict | None:
        row = (await db.execute(
            text("""
                SELECT id, max_attempts, attempts_used, is_active
                FROM exam_assignments
                WHERE assigned_by = :teacher_id
                  AND student_id  = :student_id
                  AND exam_id     = :exam_id
            """),
            {"teacher_id": str(teacher_id), "student_id": str(student_id), "exam_id": exam_id},
        )).mappings().one_or_none()
        return dict(row) if row else None

    async def upsert_assignment(
        self,
        db: AsyncSession,
        teacher_id: UUID,
        student_id: UUID,
        exam_id: int,
        max_attempts: int,
    ) -> dict:
        """
        Create a new assignment or reactivate + update an existing one.
        Returns the full assignment row.
        """
        row = (await db.execute(
            text("""
                INSERT INTO exam_assignments
                    (exam_id, student_id, assigned_by, assignment_type, max_attempts, is_active)
                VALUES
                    (:exam_id, :student_id, :teacher_id, 'assigned', :max_attempts, true)
                ON CONFLICT (exam_id, student_id)
                DO UPDATE SET
                    assigned_by   = EXCLUDED.assigned_by,
                    assignment_type = 'assigned',
                    max_attempts  = EXCLUDED.max_attempts,
                    is_active     = true
                RETURNING
                    id, exam_id, student_id, max_attempts, attempts_used,
                    is_active, created_at AS assigned_at
            """),
            {
                "exam_id": exam_id,
                "student_id": str(student_id),
                "teacher_id": str(teacher_id),
                "max_attempts": max_attempts,
            },
        )).mappings().one()
        await db.commit()

        # Fetch exam + student names for the response
        enriched = (await db.execute(
            text("""
                SELECT
                    ea.id, ea.exam_id, ea.student_id,
                    up.full_name AS student_name,
                    e.title_en   AS exam_title,
                    e.paper_code,
                    ea.max_attempts, ea.attempts_used,
                    ea.is_active, ea.created_at AS assigned_at
                FROM exam_assignments ea
                JOIN exams e       ON e.id  = ea.exam_id
                JOIN user_profiles up ON up.id = ea.student_id
                WHERE ea.id = :id
            """),
            {"id": row["id"]},
        )).mappings().one()
        return dict(enriched)

    async def get_dashboard_stats(
        self, db: AsyncSession, teacher_id: UUID
    ) -> dict:
        row = (await db.execute(
            text("""
                SELECT
                    COUNT(DISTINCT ea.student_id) AS total_students_assigned,
                    COUNT(*) FILTER (WHERE ea.is_active = true) AS total_assignments_active
                FROM exam_assignments ea
                WHERE ea.assigned_by = :teacher_id
            """),
            {"teacher_id": str(teacher_id)},
        )).mappings().one()
        return dict(row)

    async def count_active_exams(self, db: AsyncSession) -> int:
        row = (await db.execute(
            text("SELECT COUNT(*) AS cnt FROM exams WHERE is_active = true")
        )).mappings().one()
        return int(row["cnt"])

    async def find_student_by_email(
        self, db: AsyncSession, email: str
    ) -> dict | None:
        row = (await db.execute(
            text("""
                SELECT up.id, up.full_name, up.std_class, up.medium,
                       up.school_name, up.district, au.email
                FROM user_profiles up
                JOIN auth.users au ON au.id = up.id
                WHERE au.email = :email
                  AND up.role  = 'student'
                  AND up.is_active = true
            """),
            {"email": email.lower().strip()},
        )).mappings().one_or_none()
        return dict(row) if row else None


teacher_repository = TeacherRepository()
