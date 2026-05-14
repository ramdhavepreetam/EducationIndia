from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.modules.analysis.schemas import ResponseData, ReportSchema, ReportFreeSchema
from app.modules.analysis.scorer import (
    calculate_total_score,
    calculate_section_scores,
    calculate_topic_scores,
    calculate_time_analysis
)
from app.modules.analysis.recommender import generate_recommendations
from app.modules.attempt.repository import attempt_repository
from app.shared.exceptions import NotFound, Forbidden

class AnalysisService:
    async def generate_report(self, attempt_id: UUID, db: AsyncSession) -> dict:
        """
        Called by attempt.service.submit_exam() after submission.
        Does NOT write to DB.
        """
        # 1. Load attempt and responses
        attempt = await attempt_repository.get_attempt_by_id(db, attempt_id)
        if not attempt:
            raise NotFound(f"Attempt {attempt_id} not found")
            
        responses = await attempt_repository.get_all_responses(db, attempt_id)
        
        # 2. Get question data (correct_option, correct_options, topic, section)
        query = text("""
            SELECT q.id, q.question_no, q.correct_option, q.correct_options, q.marks,
                   q.topic_id, t.name_en as topic_name_en, t.name_mr as topic_name_mr,
                   q.section_id, s.section_label, s.subject_en, q.is_multi_select
            FROM questions q
            JOIN topics t ON q.topic_id = t.id
            JOIN sections s ON q.section_id = s.id
            WHERE q.exam_id = :exam_id
        """)
        result = await db.execute(query, {"exam_id": attempt.exam_id})
        q_data = {row.id: row for row in result.fetchall()}
        
        # 3. Build list[ResponseData]
        response_data_list = []
        for r in responses:
            qd = q_data.get(r.question_id)
            if not qd:
                continue
                
            response_data_list.append(ResponseData(
                question_no=qd.question_no,
                question_id=r.question_id,
                selected_option=r.selected_option,
                selected_options=r.selected_options,
                is_multi_select=qd.is_multi_select,
                correct_option=qd.correct_option,
                correct_options=list(qd.correct_options) if qd.correct_options else None,
                topic_id=qd.topic_id,
                topic_name_en=qd.topic_name_en,
                topic_name_mr=qd.topic_name_mr,
                section_id=qd.section_id,
                section_label=qd.section_label,
                subject_en=qd.subject_en,
                marks=qd.marks,
                time_taken_seconds=r.time_taken_seconds
            ))
            
        # Add skipped questions that weren't in responses
        responded_qids = {r.question_id for r in responses}
        for q_id, qd in q_data.items():
            if q_id not in responded_qids:
                response_data_list.append(ResponseData(
                    question_no=qd.question_no,
                    question_id=q_id,
                    selected_option=None,
                    selected_options=None,
                    is_multi_select=qd.is_multi_select,
                    correct_option=qd.correct_option,
                    correct_options=list(qd.correct_options) if qd.correct_options else None,
                    topic_id=qd.topic_id,
                    topic_name_en=qd.topic_name_en,
                    topic_name_mr=qd.topic_name_mr,
                    section_id=qd.section_id,
                    section_label=qd.section_label,
                    subject_en=qd.subject_en,
                    marks=qd.marks,
                    time_taken_seconds=None
                ))

        # 4-7. Call scorers
        total_score_data = calculate_total_score(response_data_list)
        section_scores = calculate_section_scores(response_data_list)
        topic_scores = calculate_topic_scores(response_data_list)
        time_analysis = calculate_time_analysis(response_data_list)
        
        # 8. Call recommender
        recommendations = generate_recommendations(topic_scores, section_scores, time_analysis)
        
        # 9. Return combined dict
        return {
            **total_score_data,
            "section_scores": section_scores,
            "topic_scores": topic_scores,
            "time_analysis": time_analysis,
            "recommendations": recommendations
        }

    async def get_attempt_report(self, attempt_id: UUID, user_id: UUID, role: str, db: AsyncSession) -> ReportSchema:
        """For the result page — reads JSONB from attempts table."""
        attempt = await attempt_repository.get_attempt_by_id(db, attempt_id)
        if not attempt:
            raise NotFound("Attempt not found")
            
        current_status = str(attempt.status.value if hasattr(attempt.status, "value") else attempt.status)
        if current_status != "submitted":
            raise Forbidden("Report is only available for submitted attempts")

        if role == "student":
            if attempt.student_id != user_id:
                raise Forbidden("Not authorized to view this report")
        elif role == "parent":
            # Check parent owns the child profile on this attempt (ADR-013)
            if attempt.child_profile_id:
                from app.modules.user.child_repository import ChildRepository
                child_repo = ChildRepository()
                is_owner = await child_repo.validate_ownership(
                    attempt.child_profile_id, user_id, db
                )
                if not is_owner:
                    raise Forbidden("Not authorized to view this report")
            else:
                raise Forbidden("Not authorized to view this report")
        elif role not in ("exam_admin", "super_admin"):
            raise Forbidden("Not authorized to view this report")

        # Access control gate (ADR-014)
        from app.shared.access_control import get_access_context, can_see_full_analysis, get_tier
        ctx = await get_access_context(user_id, db) if role == "parent" else None

        if role == "parent" and ctx is not None and not can_see_full_analysis(ctx):
            return ReportFreeSchema(
                attempt_id=str(attempt.id),
                exam_id=attempt.exam_id,
                status=current_status,
                attempt_number=attempt.attempt_number,
                submitted_at=attempt.submitted_at.isoformat() if attempt.submitted_at else "",
                total_score=attempt.total_score or 0,
                total_correct=attempt.total_correct or 0,
                total_wrong=attempt.total_wrong or 0,
                total_skipped=attempt.total_skipped or 0,
                percentage=float(attempt.percentage or 0.0),
                grade=attempt.grade or "",
            )

        # admins bypass the restriction

        return ReportSchema(
            attempt_id=str(attempt.id),
            exam_id=attempt.exam_id,
            status=current_status,
            attempt_number=attempt.attempt_number,
            submitted_at=attempt.submitted_at.isoformat() if attempt.submitted_at else "",
            total_score=attempt.total_score or 0,
            total_correct=attempt.total_correct or 0,
            total_wrong=attempt.total_wrong or 0,
            total_skipped=attempt.total_skipped or 0,
            percentage=float(attempt.percentage or 0.0),
            grade=attempt.grade or "",
            section_scores=attempt.section_scores or [],
            topic_scores=attempt.topic_scores or [],
            time_analysis=attempt.time_analysis or {},
            recommendations=attempt.recommendations or [],
            tier=get_tier(ctx) if role == "parent" and ctx is not None else "paid",
        )

# singleton
analysis_service = AnalysisService()
