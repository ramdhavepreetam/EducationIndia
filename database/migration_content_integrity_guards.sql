-- ============================================================================
-- Content integrity guards for the question bank
--
-- WHY: A 2026-08-17 audit found the PDF import pipeline silently produced
-- unanswerable questions:
--   * 396 questions typed image_only/text_image/context_image with NULL
--     question_image_url  -> renders as a blank box
--   * 1,510 options with no text and no image, of which 375 were the
--     CORRECT answer -> the student cannot possibly answer correctly
--   * 14 questions with neither stem text nor stem image
--
-- These constraints stop NEW bad data at the database boundary. They are added
-- NOT VALID on purpose: the existing backlog above still violates them, and a
-- validating constraint could not be added at all without first repairing or
-- deleting real content. NOT VALID enforces on INSERT/UPDATE immediately while
-- leaving historical rows untouched.
--
-- To validate a constraint once its backlog is repaired (takes a brief
-- ACCESS EXCLUSIVE lock, so run off-peak):
--   ALTER TABLE questions VALIDATE CONSTRAINT questions_stem_present_chk;
--
-- Idempotent: safe to re-run. Follows the project convention of
-- DROP ... IF EXISTS followed by ADD.
-- ============================================================================

-- ── questions: every question needs something to show the student ───────────
-- A question must carry stem text (either language) or a stem image.
--
-- Two exemptions:
--   * cancelled questions — withdrawn from scoring, may legitimately be retained
--     as empty placeholders matching an official answer key
--   * context-bound questions (context_id IS NOT NULL) — a context_image item
--     draws its stem and figure from the shared question_contexts row, so the
--     question row itself is intentionally bare. importer.py permits this, and
--     the constraint must agree or valid imports would be rejected.
ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_stem_present_chk;
ALTER TABLE questions
    ADD CONSTRAINT questions_stem_present_chk CHECK (
        COALESCE(is_cancelled, false)
        OR context_id IS NOT NULL
        OR COALESCE(text_en, '') <> ''
        OR COALESCE(text_mr, '') <> ''
        OR question_image_url IS NOT NULL
    ) NOT VALID;

-- ── questions: image-typed questions must actually have an image ────────────
-- image_only / text_image / context_image all render an image in the stem.
-- context_image is exempt when the image lives on the shared context row
-- (question_contexts.image_url) rather than on the question itself.
ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_image_type_has_image_chk;
ALTER TABLE questions
    ADD CONSTRAINT questions_image_type_has_image_chk CHECK (
        COALESCE(is_cancelled, false)
        OR question_type NOT IN ('image_only', 'text_image')
        OR question_image_url IS NOT NULL
    ) NOT VALID;

-- ── options: every option needs something to show the student ──────────────
-- An option must carry text (either language) or an image. This is the guard
-- that would have caught the 375 blank correct answers.
ALTER TABLE options DROP CONSTRAINT IF EXISTS options_content_present_chk;
ALTER TABLE options
    ADD CONSTRAINT options_content_present_chk CHECK (
        COALESCE(text_en, '') <> ''
        OR COALESCE(text_mr, '') <> ''
        OR image_url IS NOT NULL
    ) NOT VALID;


-- ============================================================================
-- Paper health view — surfaces broken papers before students see them.
--
-- Admin-facing. One row per exam with counts of each defect class.
-- publish_blocker_count is the number that makes a paper unfit to publish:
-- a question whose correct answer is blank can never be answered correctly.
-- ============================================================================
CREATE OR REPLACE VIEW v_paper_health AS
SELECT
    e.id                        AS exam_id,
    ev.year,
    e.paper_code,
    e.set_code,
    e.is_active,
    COUNT(DISTINCT q.id)        AS total_questions,
    COUNT(DISTINCT q.id) FILTER (WHERE COALESCE(q.is_cancelled, false)) AS cancelled_questions,
    -- image-typed question with no image attached
    COUNT(DISTINCT q.id) FILTER (
        WHERE NOT COALESCE(q.is_cancelled, false)
          AND q.question_type IN ('image_only', 'text_image', 'context_image')
          AND q.question_image_url IS NULL
    )                           AS missing_image_count,
    -- question with neither stem text nor stem image
    COUNT(DISTINCT q.id) FILTER (
        WHERE NOT COALESCE(q.is_cancelled, false)
          AND COALESCE(q.text_en, '') = ''
          AND COALESCE(q.text_mr, '') = ''
          AND q.question_image_url IS NULL
    )                           AS missing_stem_count,
    -- any blank option (degrades the question but may still be answerable)
    COUNT(DISTINCT q.id) FILTER (
        WHERE NOT COALESCE(q.is_cancelled, false)
          AND o.id IS NOT NULL
          AND COALESCE(o.text_en, '') = ''
          AND COALESCE(o.text_mr, '') = ''
          AND o.image_url IS NULL
    )                           AS blank_option_count,
    -- the correct answer itself is blank -> unanswerable. Publish blocker.
    COUNT(DISTINCT q.id) FILTER (
        WHERE NOT COALESCE(q.is_cancelled, false)
          AND o.is_correct
          AND COALESCE(o.text_en, '') = ''
          AND COALESCE(o.text_mr, '') = ''
          AND o.image_url IS NULL
    )                           AS blank_correct_answer_count,
    COUNT(DISTINCT q.id) FILTER (
        WHERE NOT COALESCE(q.is_cancelled, false)
          AND (
            (o.is_correct
             AND COALESCE(o.text_en, '') = ''
             AND COALESCE(o.text_mr, '') = ''
             AND o.image_url IS NULL)
            OR (COALESCE(q.text_en, '') = ''
                AND COALESCE(q.text_mr, '') = ''
                AND q.question_image_url IS NULL)
          )
    )                           AS publish_blocker_count
FROM exams e
JOIN exam_events ev ON ev.id = e.event_id
LEFT JOIN questions q ON q.exam_id = e.id
LEFT JOIN options   o ON o.question_id = q.id
GROUP BY e.id, ev.year, e.paper_code, e.set_code, e.is_active;

COMMENT ON VIEW v_paper_health IS
    'Admin content-QA view. publish_blocker_count > 0 means the paper has questions '
    'that cannot be answered correctly and must not be published. Added 2026-08-17.';
