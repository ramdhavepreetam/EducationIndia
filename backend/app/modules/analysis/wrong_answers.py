"""
Wrong answers summary builder — reusable by any module.

Queries v_exam_answers view (post-submission only) joined with responses
to find wrong answers and return them with question text + options + explanation.

NOTE: We compare selected_option != correct_option directly, rather than
relying on responses.is_correct, because that column may not be populated
for all attempts.

Used by:
  - parent_service.get_attempt_wrong_answers()
  - parent_service.get_recent_mistakes_summary()
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analysis.schemas import (
    OptionItemSchema,
    WrongAnswerItem,
    WrongAnswersSummary,
)


async def build_wrong_answers_summary(
    attempt_id: UUID,
    db: AsyncSession,
    include_details: bool = True,
    limit: Optional[int] = None,
) -> WrongAnswersSummary:
    """
    Build a summary of wrong answers for a submitted attempt.

    Args:
        attempt_id: UUID of the attempt (must be submitted).
        db: Async database session.
        include_details: If False (free tier), returns only total_wrong count.
        limit: Optional cap on number of wrong items returned (e.g. 5 for dashboard).

    Returns:
        WrongAnswersSummary with total_wrong, total_skipped, and optionally items list.
    """
    # Get the exam_id for this attempt (needed for v_exam_answers join)
    exam_result = await db.execute(
        text("SELECT exam_id FROM attempts WHERE id = :attempt_id"),
        {"attempt_id": str(attempt_id)},
    )
    exam_id = exam_result.scalar()
    if not exam_id:
        return WrongAnswersSummary(total_wrong=0, total_skipped=0, items=[])

    # Count wrong + skipped in one query (always returned, even for free tier)
    counts_result = await db.execute(
        text("""
            SELECT
                COUNT(CASE
                    WHEN r.selected_option IS NOT NULL
                     AND r.selected_option != va.correct_option
                    THEN 1
                END) AS total_wrong,
                COUNT(CASE
                    WHEN r.selected_option IS NULL
                    THEN 1
                END) AS total_skipped
            FROM responses r
            JOIN v_exam_answers va
              ON va.question_id = r.question_id
             AND va.exam_id = :exam_id
            WHERE r.attempt_id = :attempt_id
        """),
        {"attempt_id": str(attempt_id), "exam_id": exam_id},
    )
    counts = counts_result.mappings().first()
    total_wrong = counts["total_wrong"] if counts else 0
    total_skipped = counts["total_skipped"] if counts else 0

    # Free tier: return counts only, no items
    if not include_details:
        return WrongAnswersSummary(
            total_wrong=total_wrong, total_skipped=total_skipped, items=[]
        )

    # Paid tier: fetch wrong answer details
    limit_clause = f"LIMIT {int(limit)}" if limit else ""
    result = await db.execute(
        text(f"""
            SELECT
                r.question_no,
                r.selected_option,
                q.text_en          AS question_text_en,
                q.text_mr          AS question_text_mr,
                va.correct_option,
                va.explanation_en,
                va.explanation_mr,
                q.question_image_url,
                s.subject_en       AS section_subject_en,
                s.section_label,
                s.subject_mr       AS subject_mr,
                t.name_en          AS topic_name_en,
                t.name_mr          AS topic_name_mr
            FROM responses r
            JOIN questions q       ON q.id = r.question_id
            JOIN v_exam_answers va ON va.question_id = r.question_id
                                  AND va.exam_id = :exam_id
            LEFT JOIN sections s   ON s.id = q.section_id
            LEFT JOIN topics t     ON t.id = q.topic_id
            WHERE r.attempt_id = :attempt_id
              AND r.selected_option IS NOT NULL
              AND r.selected_option != va.correct_option
            ORDER BY r.question_no ASC
            {limit_clause}
        """),
        {"attempt_id": str(attempt_id), "exam_id": exam_id},
    )
    wrong_rows = result.mappings().all()

    # Fetch options for all wrong questions in one query
    question_nos = [row["question_no"] for row in wrong_rows]
    if not question_nos:
        return WrongAnswersSummary(
            total_wrong=total_wrong, total_skipped=total_skipped, items=[]
        )

    options_result = await db.execute(
        text("""
            SELECT
                o.option_no,
                o.text_en,
                o.text_mr,
                o.image_url,
                o.is_correct,
                q.question_no
            FROM options o
            JOIN questions q ON q.id = o.question_id
            WHERE q.exam_id = :exam_id
              AND q.question_no = ANY(:question_nos)
            ORDER BY q.question_no, o.option_no
        """),
        {"exam_id": exam_id, "question_nos": question_nos},
    )
    options_rows = options_result.mappings().all()

    # Group options by question_no
    options_by_qno: dict[int, list[OptionItemSchema]] = {}
    for opt in options_rows:
        qno = opt["question_no"]
        if qno not in options_by_qno:
            options_by_qno[qno] = []
        options_by_qno[qno].append(
            OptionItemSchema(
                option_no=opt["option_no"],
                text_en=opt["text_en"],
                text_mr=opt["text_mr"],
                image_url=opt["image_url"],
                is_correct=opt["is_correct"],
            )
        )

    # Build items
    items = []
    for row in wrong_rows:
        items.append(
            WrongAnswerItem(
                question_no=row["question_no"],
                question_text_en=row["question_text_en"],
                question_text_mr=row["question_text_mr"],
                question_image_url=row["question_image_url"],
                selected_option=row["selected_option"],
                correct_option=row["correct_option"],
                explanation_en=row["explanation_en"],
                explanation_mr=row["explanation_mr"],
                section_subject_en=row["section_subject_en"],
                section_label=row["section_label"],
                subject_mr=row["subject_mr"],
                topic_name_en=row["topic_name_en"],
                topic_name_mr=row["topic_name_mr"],
                options=options_by_qno.get(row["question_no"], []),
            )
        )

    return WrongAnswersSummary(
        total_wrong=total_wrong, total_skipped=total_skipped, items=items
    )
