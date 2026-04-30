"""
Question module repository — ALL database queries live here.

Delivery queries use v_exam_questions view (EXCLUDES correct_option + explanation).
Review/admin queries use the questions table directly.
Options are always loaded separately and assembled in this layer.

SECURITY: fetch_by_exam_id and fetch_by_id_for_delivery NEVER touch
questions.correct_option — the view enforces this at the DB level.
"""

from uuid import UUID

from sqlalchemy import select, text, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.question.models import Option, Question, QuestionContext
from app.modules.question.schemas import (
    BulkImportSchema,
    ContextSchema,
    OptionDeliverySchema,
    OptionReviewSchema,
    QuestionAdminSchema,
    QuestionDeliverySchema,
    QuestionReviewSchema,
)

# Columns to SELECT from v_exam_questions for delivery.
# Explicit list — never use SELECT * to prevent accidental correct_option leakage.
_DELIVERY_COLS = """
    id, exam_id, section_id, topic_id, context_id, question_no, question_type,
    text_en, text_mr, question_image_url, question_image_alt_en, question_image_alt_mr,
    marks, difficulty, tags, is_multi_select
"""


class QuestionRepository:

    # ── Delivery queries (view — no correct_option) ───────────────────────────

    async def fetch_by_exam_id(
        self, db: AsyncSession, exam_id: int
    ) -> list[QuestionDeliverySchema]:
        """
        Fetch all questions for an exam using the v_exam_questions view.
        SECURITY: view excludes correct_option and explanation at DB level.
        Returns assembled QuestionDeliverySchema list with options + contexts.
        """
        # Step 1: Questions from view (no correct_option in view columns)
        rows = (
            await db.execute(
                text(
                    f"SELECT {_DELIVERY_COLS} FROM v_exam_questions"
                    " WHERE exam_id = :eid ORDER BY question_no"
                ),
                {"eid": exam_id},
            )
        ).mappings().all()

        if not rows:
            return []

        # Step 2: Options for all questions in one query
        q_ids = [r["id"] for r in rows]
        opts_result = await db.execute(
            select(Option)
            .where(Option.question_id.in_(q_ids))
            .order_by(Option.question_id, Option.option_no)
        )
        opts_map: dict[int, list[Option]] = {}
        for opt in opts_result.scalars().all():
            opts_map.setdefault(opt.question_id, []).append(opt)

        # Step 3: Contexts (only for questions that have one)
        ctx_ids = [r["context_id"] for r in rows if r["context_id"] is not None]
        ctx_map: dict[int, QuestionContext] = {}
        if ctx_ids:
            ctxs = (
                await db.execute(
                    select(QuestionContext).where(QuestionContext.id.in_(ctx_ids))
                )
            ).scalars().all()
            ctx_map = {c.id: c for c in ctxs}

        # Step 4: Assemble Pydantic delivery schemas
        result = []
        for r in rows:
            opts_schema = [
                OptionDeliverySchema.model_validate(o, from_attributes=True)
                for o in opts_map.get(r["id"], [])
            ]
            ctx = ctx_map.get(r["context_id"]) if r["context_id"] else None
            ctx_schema = ContextSchema.model_validate(ctx, from_attributes=True) if ctx else None

            result.append(
                QuestionDeliverySchema(
                    id=r["id"],
                    exam_id=r["exam_id"],
                    section_id=r["section_id"],
                    topic_id=r["topic_id"],
                    context_id=r["context_id"],
                    question_no=r["question_no"],
                    question_type=r["question_type"],
                    text_en=r["text_en"],
                    text_mr=r["text_mr"],
                    question_image_url=r["question_image_url"],
                    question_image_alt_en=r["question_image_alt_en"],
                    question_image_alt_mr=r["question_image_alt_mr"],
                    marks=r["marks"],
                    difficulty=r["difficulty"],
                    tags=r["tags"] or [],
                    is_multi_select=r["is_multi_select"],
                    options=opts_schema,
                    context=ctx_schema,
                )
            )
        return result

    async def fetch_by_id_for_delivery(
        self, db: AsyncSession, question_id: int
    ) -> QuestionDeliverySchema | None:
        """
        Fetch a single question from v_exam_questions view.
        SECURITY: view excludes correct_option at DB level.
        """
        row = (
            await db.execute(
                text(
                    f"SELECT {_DELIVERY_COLS} FROM v_exam_questions WHERE id = :qid"
                ),
                {"qid": question_id},
            )
        ).mappings().first()

        if not row:
            return None

        opts_result = await db.execute(
            select(Option)
            .where(Option.question_id == question_id)
            .order_by(Option.option_no)
        )
        opts_schema = [
            OptionDeliverySchema.model_validate(o, from_attributes=True)
            for o in opts_result.scalars().all()
        ]

        ctx = None
        if row["context_id"]:
            ctx_row = (
                await db.execute(
                    select(QuestionContext).where(QuestionContext.id == row["context_id"])
                )
            ).scalar_one_or_none()
            ctx = ContextSchema.model_validate(ctx_row, from_attributes=True) if ctx_row else None

        return QuestionDeliverySchema(
            id=row["id"],
            exam_id=row["exam_id"],
            section_id=row["section_id"],
            topic_id=row["topic_id"],
            context_id=row["context_id"],
            question_no=row["question_no"],
            question_type=row["question_type"],
            text_en=row["text_en"],
            text_mr=row["text_mr"],
            question_image_url=row["question_image_url"],
            question_image_alt_en=row["question_image_alt_en"],
            question_image_alt_mr=row["question_image_alt_mr"],
            marks=row["marks"],
            difficulty=row["difficulty"],
            tags=row["tags"] or [],
            is_multi_select=row["is_multi_select"],
            options=opts_schema,
            context=ctx,
        )

    # ── Review query (questions table — includes correct_option) ──────────────

    async def fetch_by_id_for_review(
        self, db: AsyncSession, question_id: int
    ) -> QuestionReviewSchema | None:
        """
        Fetch full question data for post-exam review.
        Queries questions table directly (includes correct_option + explanation).
        MUST only be called after attempt.status == 'submitted' check in service layer.
        """
        result = await db.execute(
            select(Question)
            .options(selectinload(Question.options), selectinload(Question.context))
            .where(Question.id == question_id)
        )
        q = result.scalar_one_or_none()
        if not q:
            return None

        opts_schema = [
            OptionReviewSchema.model_validate(o, from_attributes=True)
            for o in q.options
        ]
        ctx_schema = (
            ContextSchema.model_validate(q.context, from_attributes=True)
            if q.context
            else None
        )

        return QuestionReviewSchema(
            id=q.id,
            exam_id=q.exam_id,
            section_id=q.section_id,
            topic_id=q.topic_id,
            context_id=q.context_id,
            question_no=q.question_no,
            question_type=q.question_type,
            text_en=q.text_en,
            text_mr=q.text_mr,
            question_image_url=q.question_image_url,
            question_image_alt_en=q.question_image_alt_en,
            question_image_alt_mr=q.question_image_alt_mr,
            marks=q.marks,
            difficulty=q.difficulty,
            tags=q.tags or [],
            correct_option=q.correct_option,
            correct_options=q.correct_options,
            is_multi_select=q.is_multi_select,
            explanation_en=q.explanation_en,
            explanation_mr=q.explanation_mr,
            options=opts_schema,
            context=ctx_schema,
        )

    # ── Admin query (full data) ───────────────────────────────────────────────

    async def fetch_by_id_for_admin(
        self, db: AsyncSession, question_id: int
    ) -> QuestionAdminSchema | None:
        """Full question data for admin edit panel — includes hints and stats."""
        result = await db.execute(
            select(Question)
            .options(selectinload(Question.options), selectinload(Question.context))
            .where(Question.id == question_id)
        )
        q = result.scalar_one_or_none()
        if not q:
            return None

        opts_schema = [
            OptionReviewSchema.model_validate(o, from_attributes=True)
            for o in q.options
        ]
        ctx_schema = (
            ContextSchema.model_validate(q.context, from_attributes=True)
            if q.context
            else None
        )

        return QuestionAdminSchema(
            id=q.id,
            exam_id=q.exam_id,
            section_id=q.section_id,
            topic_id=q.topic_id,
            context_id=q.context_id,
            question_no=q.question_no,
            question_type=q.question_type,
            text_en=q.text_en,
            text_mr=q.text_mr,
            question_image_url=q.question_image_url,
            question_image_alt_en=q.question_image_alt_en,
            question_image_alt_mr=q.question_image_alt_mr,
            correct_option=q.correct_option,
            correct_options=q.correct_options,
            is_multi_select=q.is_multi_select,
            explanation_en=q.explanation_en,
            explanation_mr=q.explanation_mr,
            hint_en=q.hint_en,
            hint_mr=q.hint_mr,
            marks=q.marks,
            difficulty=q.difficulty,
            tags=q.tags or [],
            attempt_count=q.attempt_count,
            correct_count=q.correct_count,
            actual_difficulty_ratio=float(q.actual_difficulty_ratio) if q.actual_difficulty_ratio else None,
            options=opts_schema,
            context=ctx_schema,
        )

    async def fetch_admin_list(
        self, db: AsyncSession, exam_id: int
    ) -> list[Question]:
        """Return all questions for an exam (admin view). ORM objects."""
        result = await db.execute(
            select(Question)
            .options(selectinload(Question.options))
            .where(Question.exam_id == exam_id)
            .order_by(Question.question_no)
        )
        return list(result.scalars().all())

    # ── Attempt status check (cross-module — temp until attempt module built) ─

    async def get_attempt_status(
        self, db: AsyncSession, attempt_id: UUID
    ) -> dict | None:
        """
        Check attempt status and owner. Used by service.get_question_for_review().
        TODO: Replace with attempt_service.get_attempt() once attempt module is built.
        """
        row = (
            await db.execute(
                text(
                    "SELECT status, student_id FROM attempts WHERE id = :aid"
                ),
                {"aid": str(attempt_id)},
            )
        ).mappings().first()
        return dict(row) if row else None

    # ── Admin mutations ───────────────────────────────────────────────────────

    async def update_question(
        self, db: AsyncSession, question_id: int, updates: dict
    ) -> Question | None:
        """Apply partial updates to a question row."""
        if not updates:
            return await self._get_question_by_id(db, question_id)
        await db.execute(
            sa_update(Question).where(Question.id == question_id).values(**updates)
        )
        await db.flush()
        return await self._get_question_by_id(db, question_id)

    async def delete_question(self, db: AsyncSession, question_id: int) -> bool:
        """Hard delete a question. Returns True if deleted."""
        q = await self._get_question_by_id(db, question_id)
        if not q:
            return False
        await db.delete(q)
        await db.flush()
        return True

    async def _get_question_by_id(
        self, db: AsyncSession, question_id: int
    ) -> Question | None:
        result = await db.execute(
            select(Question).where(Question.id == question_id)
        )
        return result.scalar_one_or_none()

    # ── Bulk insert ───────────────────────────────────────────────────────────

    async def bulk_insert(
        self, db: AsyncSession, import_data: BulkImportSchema
    ) -> tuple[int, list[str]]:
        """
        Insert contexts, questions, and options in one transaction.
        Returns (inserted_count, error_list).
        Context_ref indices in questions are resolved to real DB IDs.
        """
        inserted = 0
        errors: list[str] = []

        # Step 1: Insert contexts and build index → DB id mapping
        ctx_id_map: dict[int, int] = {}  # {context_ref_index: db_context_id}
        for idx, ctx_item in enumerate(import_data.contexts):
            ctx = QuestionContext(
                exam_id=import_data.exam_id,
                context_type=ctx_item.context_type,
                title_en=ctx_item.title_en,
                title_mr=ctx_item.title_mr,
                content_en=ctx_item.content_en,
                content_mr=ctx_item.content_mr,
                image_url=ctx_item.image_url,
                image_alt_en=ctx_item.image_alt_en,
                image_alt_mr=ctx_item.image_alt_mr,
                instruction_en=ctx_item.instruction_en,
                instruction_mr=ctx_item.instruction_mr,
                applies_from=ctx_item.applies_from,
                applies_to=ctx_item.applies_to,
                order_index=ctx_item.order_index,
            )
            db.add(ctx)
            await db.flush()  # populate ctx.id
            ctx_id_map[idx] = ctx.id

        # Step 2: Insert questions + options
        for q_item in import_data.questions:
            try:
                context_id = (
                    ctx_id_map[q_item.context_ref]
                    if q_item.context_ref is not None
                    else None
                )
                q = Question(
                    exam_id=import_data.exam_id,
                    section_id=q_item.section_id,
                    topic_id=q_item.topic_id,
                    context_id=context_id,
                    question_no=q_item.question_no,
                    question_type=q_item.question_type,
                    text_en=q_item.text_en,
                    text_mr=q_item.text_mr,
                    question_image_url=q_item.question_image_url,
                    question_image_alt_en=q_item.question_image_alt_en,
                    question_image_alt_mr=q_item.question_image_alt_mr,
                    correct_option=q_item.correct_option,
                    correct_options=q_item.correct_options,
                    is_multi_select=q_item.is_multi_select,
                    explanation_en=q_item.explanation_en,
                    explanation_mr=q_item.explanation_mr,
                    hint_en=q_item.hint_en,
                    hint_mr=q_item.hint_mr,
                    marks=q_item.marks,
                    difficulty=q_item.difficulty,
                    tags=q_item.tags,
                )
                db.add(q)
                await db.flush()  # populate q.id

                for opt_item in q_item.options:
                    opt = Option(
                        question_id=q.id,
                        option_no=opt_item.option_no,
                        text_en=opt_item.text_en,
                        text_mr=opt_item.text_mr,
                        image_url=opt_item.image_url,
                        image_alt_en=opt_item.image_alt_en,
                        image_alt_mr=opt_item.image_alt_mr,
                        # is_correct set by DB trigger — do not set here
                    )
                    db.add(opt)

                inserted += 1

            except Exception as e:
                errors.append(
                    f"Q{q_item.question_no}: {str(e)}"
                )

        return inserted, errors

    async def replace_exam_questions(
        self, db: AsyncSession, import_data: BulkImportSchema
    ) -> tuple[int, list[str]]:
        """
        Delete all existing questions (and their options + contexts) for the exam,
        then insert the new batch. Makes bulk-import idempotent for admin re-seeding.

        Deletion order (FK constraints):
          options → questions → question_contexts (all filtered by exam_id)
        """
        # Delete options first (FK to questions)
        await db.execute(
            text(
                "DELETE FROM options WHERE question_id IN "
                "(SELECT id FROM questions WHERE exam_id = :eid)"
            ),
            {"eid": import_data.exam_id},
        )
        # Delete questions
        await db.execute(
            text("DELETE FROM questions WHERE exam_id = :eid"),
            {"eid": import_data.exam_id},
        )
        # Delete question contexts
        await db.execute(
            text("DELETE FROM question_contexts WHERE exam_id = :eid"),
            {"eid": import_data.exam_id},
        )
        await db.flush()

        return await self.bulk_insert(db, import_data)



# Module-level singleton — import this in service.py
question_repository = QuestionRepository()
