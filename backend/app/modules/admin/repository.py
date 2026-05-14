from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AdminRepository:
    async def get_student_dashboard_stats(self, db: AsyncSession, student_id: UUID) -> dict:
        row = (
            await db.execute(
                text("""
                    SELECT
                        COUNT(*) AS total_attempts,
                        COUNT(DISTINCT CASE WHEN status = 'submitted' THEN exam_id END)
                            AS exams_completed,
                        COALESCE(MAX(CASE WHEN status = 'submitted' THEN total_score END), 0)
                            AS best_score,
                        COALESCE(AVG(CASE WHEN status = 'submitted' AND percentage IS NOT NULL
                                         THEN percentage END), 0) AS avg_percentage
                    FROM attempts
                    WHERE child_profile_id = :sid OR student_id = :sid
                """),
                {"sid": str(student_id)},
            )
        ).mappings().first()
        return dict(row) if row else {}

    async def get_overview_stats(self, db: AsyncSession) -> dict:
        row = (
            await db.execute(
                text("""
                    SELECT
                      (SELECT COUNT(*) FROM user_profiles WHERE role = 'student') AS total_students,
                      (SELECT COUNT(*) FROM attempts) AS total_attempts,
                      (SELECT COUNT(*) FROM exams WHERE is_active = true) AS active_exams,
                      (SELECT COUNT(*) FROM questions) AS total_questions
                """)
            )
        ).mappings().first()
        return dict(row) if row else {}

    async def get_recent_attempts(self, db: AsyncSession, limit: int = 20) -> list[dict]:
        rows = (
            await db.execute(
                text("""
                    SELECT
                        a.id AS attempt_id,
                        COALESCE(a.student_id, a.child_profile_id) AS student_id,
                        up.full_name AS student_name,
                        a.exam_id,
                        e.title_en AS exam_title,
                        a.status,
                        a.total_score,
                        a.percentage,
                        a.grade,
                        a.started_at,
                        a.submitted_at
                    FROM attempts a
                    LEFT JOIN user_profiles up ON up.id = COALESCE(a.student_id, a.child_profile_id)
                    LEFT JOIN exams e ON e.id = a.exam_id
                    ORDER BY a.started_at DESC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    async def list_exams_admin(self, db: AsyncSession) -> list[dict]:
        rows = (
            await db.execute(
                text("""
                    SELECT
                        e.id, e.paper_code, e.set_code,
                        e.title_en, e.title_mr,
                        e.is_active, e.total_questions,
                        ev.title_en AS event_title,
                        ev.year AS event_year,
                        ev.std_class AS std_class,
                        COUNT(q.id) AS question_count
                    FROM exams e
                    LEFT JOIN exam_events ev ON ev.id = e.event_id
                    LEFT JOIN questions q ON q.exam_id = e.id
                    GROUP BY e.id, ev.id
                    ORDER BY e.id
                """)
            )
        ).mappings().all()
        return [dict(row) for row in rows]

    async def get_question_stats(self, db: AsyncSession, exam_id: int) -> list[dict]:
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
        return [dict(row) for row in rows]


admin_repository = AdminRepository()
