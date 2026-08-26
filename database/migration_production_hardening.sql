-- ScholarPath production hardening.
-- Fixes schema drift, answer-data exposure, payment/media RLS, and question stats.

-- ══════════════════════════════════════════════════════════════════════════════
-- Attempts ownership: support ADR-013 child-profile attempts.
-- ══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.attempts
    ALTER COLUMN student_id DROP NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'attempts_has_owner_check'
          AND conrelid = 'public.attempts'::regclass
    ) THEN
        ALTER TABLE public.attempts
            ADD CONSTRAINT attempts_has_owner_check
            CHECK (student_id IS NOT NULL OR child_profile_id IS NOT NULL)
            NOT VALID;
    END IF;
END $$;

ALTER TABLE public.attempts VALIDATE CONSTRAINT attempts_has_owner_check;

CREATE INDEX IF NOT EXISTS idx_attempts_child_profile_exam
    ON public.attempts(child_profile_id, exam_id)
    WHERE child_profile_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_attempts_child_profile_status
    ON public.attempts(child_profile_id, status)
    WHERE child_profile_id IS NOT NULL;

-- Parent-child RLS for ADR-013 attempts/responses.
DROP POLICY IF EXISTS "Parents read linked children attempts" ON public.attempts;
DROP POLICY IF EXISTS "Parents read child profile attempts" ON public.attempts;
CREATE POLICY "Parents read child profile attempts"
ON public.attempts
FOR SELECT
USING (
    (
        child_profile_id IN (
            SELECT cp.id
            FROM public.child_profiles cp
            WHERE cp.parent_id = (SELECT auth.uid())
              AND cp.is_active = true
        )
    )
    OR (
        student_id IS NOT NULL
        AND parent_can_see_student(student_id)
    )
);

DROP POLICY IF EXISTS "Parents read children responses" ON public.responses;
DROP POLICY IF EXISTS "Parents read child profile responses" ON public.responses;
CREATE POLICY "Parents read child profile responses"
ON public.responses
FOR SELECT
USING (
    EXISTS (
        SELECT 1
        FROM public.attempts a
        WHERE a.id = responses.attempt_id
          AND (
            a.child_profile_id IN (
                SELECT cp.id
                FROM public.child_profiles cp
                WHERE cp.parent_id = (SELECT auth.uid())
                  AND cp.is_active = true
            )
            OR (
                a.student_id IS NOT NULL
                AND parent_can_see_student(a.student_id)
            )
          )
    )
);

-- ══════════════════════════════════════════════════════════════════════════════
-- Question answer security: raw tables must not be publicly readable.
-- FastAPI serves delivery data through v_exam_questions/QuestionDeliverySchema.
-- ══════════════════════════════════════════════════════════════════════════════

DROP POLICY IF EXISTS "Anyone reads questions for active exams" ON public.questions;
DROP POLICY IF EXISTS "Anyone reads options" ON public.options;
DROP POLICY IF EXISTS "Anyone reads question contexts" ON public.question_contexts;

DROP POLICY IF EXISTS "Admins manage options" ON public.options;
CREATE POLICY "Admins manage options"
ON public.options
FOR ALL
USING (is_admin())
WITH CHECK (is_admin());

DROP POLICY IF EXISTS "Admins manage question contexts" ON public.question_contexts;
CREATE POLICY "Admins manage question contexts"
ON public.question_contexts
FOR ALL
USING (is_admin())
WITH CHECK (is_admin());

REVOKE SELECT ON public.questions FROM anon, authenticated;
REVOKE SELECT ON public.options FROM anon, authenticated;
REVOKE SELECT ON public.question_contexts FROM anon, authenticated;
REVOKE SELECT ON public.v_exam_answers FROM anon, authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.questions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.options TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.question_contexts TO authenticated;

-- ══════════════════════════════════════════════════════════════════════════════
-- Cancelled questions and multi-answer review metadata.
-- ══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.questions
    ADD COLUMN IF NOT EXISTS is_cancelled BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS cancelled_reason TEXT;

UPDATE public.questions
SET is_cancelled = false
WHERE is_cancelled IS NULL;

ALTER TABLE public.questions
    ALTER COLUMN is_cancelled SET NOT NULL;

-- DROP first: this revision inserts is_cancelled/cancelled_reason in the middle
-- of the column list, and CREATE OR REPLACE VIEW can only APPEND columns, never
-- reorder or rename them. Replacing in place fails with:
--   cannot change name of view column "explanation_en" to "is_cancelled"
-- Safe to drop: nothing depends on this view (the backend queries it directly).
DROP VIEW IF EXISTS public.v_exam_answers;

CREATE VIEW public.v_exam_answers AS
SELECT
    q.id AS question_id,
    q.exam_id,
    q.question_no,
    q.correct_option,
    q.correct_options,
    q.is_multi_select,
    q.is_cancelled,
    q.cancelled_reason,
    q.explanation_en,
    q.explanation_mr,
    q.hint_en,
    q.hint_mr
FROM public.questions q;

ALTER VIEW public.v_exam_answers SET (security_invoker = true);
REVOKE SELECT ON public.v_exam_answers FROM anon, authenticated;

CREATE OR REPLACE FUNCTION public.sync_correct_option() RETURNS TRIGGER AS $$
BEGIN
    IF COALESCE(NEW.is_cancelled, false) THEN
        UPDATE public.options
        SET is_correct = false
        WHERE question_id = NEW.id;
    ELSIF NEW.is_multi_select THEN
        UPDATE public.options
        SET is_correct = (option_no = ANY(NEW.correct_options))
        WHERE question_id = NEW.id;
    ELSE
        UPDATE public.options
        SET is_correct = (option_no = NEW.correct_option)
        WHERE question_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

ALTER FUNCTION public.sync_correct_option() SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS sync_correct_option_trigger ON public.questions;
CREATE TRIGGER sync_correct_option_trigger
AFTER INSERT OR UPDATE OF correct_option, correct_options, is_multi_select, is_cancelled
ON public.questions
FOR EACH ROW
EXECUTE FUNCTION public.sync_correct_option();

-- ══════════════════════════════════════════════════════════════════════════════
-- Media metadata table used by the media module.
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.media_files (
    id                SERIAL PRIMARY KEY,
    uploaded_by       UUID REFERENCES public.user_profiles(id) ON DELETE SET NULL,
    file_type         VARCHAR(50) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_key       TEXT NOT NULL,
    file_url          TEXT NOT NULL,
    content_type      VARCHAR(100),
    file_size         INT,
    is_active         BOOLEAN NOT NULL DEFAULT true,
    created_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_media_files_uploaded_by
    ON public.media_files(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_media_files_active
    ON public.media_files(is_active)
    WHERE is_active = true;

ALTER TABLE public.media_files ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users read own media files" ON public.media_files;
CREATE POLICY "Users read own media files"
ON public.media_files
FOR SELECT
USING (uploaded_by = (SELECT auth.uid()));

DROP POLICY IF EXISTS "Admins manage media files" ON public.media_files;
CREATE POLICY "Admins manage media files"
ON public.media_files
FOR ALL
USING (is_admin())
WITH CHECK (is_admin());

-- ══════════════════════════════════════════════════════════════════════════════
-- Payment and app-settings RLS.
-- ══════════════════════════════════════════════════════════════════════════════

ALTER TABLE public.app_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone reads public app settings" ON public.app_settings;
CREATE POLICY "Anyone reads public app settings"
ON public.app_settings
FOR SELECT
USING (
    key IN (
        'razorpay_key_id',
        'app_name',
        'support_email',
        'maintenance_mode',
        'new_registrations',
        'free_tier_exam_id',
        'free_tier_max_attempts'
    )
);

DROP POLICY IF EXISTS "Admins manage app settings" ON public.app_settings;
CREATE POLICY "Admins manage app settings"
ON public.app_settings
FOR ALL
USING (is_admin())
WITH CHECK (is_admin());

DROP POLICY IF EXISTS "Parents read own subscriptions" ON public.subscriptions;
CREATE POLICY "Parents read own subscriptions"
ON public.subscriptions
FOR SELECT
USING (parent_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS "Admins manage subscriptions" ON public.subscriptions;
CREATE POLICY "Admins manage subscriptions"
ON public.subscriptions
FOR ALL
USING (is_admin())
WITH CHECK (is_admin());

DROP POLICY IF EXISTS "Parents read own payments" ON public.payments;
CREATE POLICY "Parents read own payments"
ON public.payments
FOR SELECT
USING (parent_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS "Admins manage payments" ON public.payments;
CREATE POLICY "Admins manage payments"
ON public.payments
FOR ALL
USING (is_admin())
WITH CHECK (is_admin());

-- ══════════════════════════════════════════════════════════════════════════════
-- Correct question_stats from canonical question answers, not responses.is_correct.
-- ══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.update_question_stats_on_submit() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'submitted' AND OLD.status = 'ongoing' THEN
        INSERT INTO public.question_stats (
            question_id,
            total_attempts,
            correct_count,
            wrong_count,
            skip_count,
            avg_time_seconds
        )
        WITH scored AS (
            SELECT
                q.id AS question_id,
                COALESCE(r.time_taken_seconds, 0) AS time_taken_seconds,
                CASE
                    WHEN q.is_multi_select THEN
                        r.selected_options IS NOT NULL
                        AND cardinality(r.selected_options) > 0
                    ELSE
                        r.selected_option IS NOT NULL
                END AS is_answered,
                CASE
                    WHEN q.is_multi_select THEN
                        r.selected_options IS NOT NULL
                        AND q.correct_options IS NOT NULL
                        AND r.selected_options @> q.correct_options
                        AND r.selected_options <@ q.correct_options
                    WHEN q.correct_options IS NOT NULL THEN
                        r.selected_option = ANY(q.correct_options)
                    ELSE
                        r.selected_option = q.correct_option
                END AS is_correct
            FROM public.questions q
            LEFT JOIN public.responses r
              ON r.question_id = q.id
             AND r.attempt_id = NEW.id
            WHERE q.exam_id = NEW.exam_id
              AND COALESCE(q.is_cancelled, false) = false
        )
        SELECT
            question_id,
            1,
            CASE WHEN is_answered AND is_correct THEN 1 ELSE 0 END,
            CASE WHEN is_answered AND NOT is_correct THEN 1 ELSE 0 END,
            CASE WHEN NOT is_answered THEN 1 ELSE 0 END,
            time_taken_seconds
        FROM scored
        ON CONFLICT (question_id) DO UPDATE
        SET total_attempts = public.question_stats.total_attempts + EXCLUDED.total_attempts,
            correct_count = public.question_stats.correct_count + EXCLUDED.correct_count,
            wrong_count = public.question_stats.wrong_count + EXCLUDED.wrong_count,
            skip_count = public.question_stats.skip_count + EXCLUDED.skip_count,
            avg_time_seconds = (
                (
                    public.question_stats.avg_time_seconds * public.question_stats.total_attempts
                    + EXCLUDED.avg_time_seconds * EXCLUDED.total_attempts
                ) / NULLIF(public.question_stats.total_attempts + EXCLUDED.total_attempts, 0)
            ),
            actual_difficulty = CASE
                WHEN (public.question_stats.total_attempts + EXCLUDED.total_attempts) > 0
                THEN (
                    public.question_stats.wrong_count + EXCLUDED.wrong_count
                )::NUMERIC / (
                    public.question_stats.total_attempts + EXCLUDED.total_attempts
                )
                ELSE 0
            END,
            updated_at = now();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

ALTER FUNCTION public.update_question_stats_on_submit() SET search_path = public, pg_temp;
