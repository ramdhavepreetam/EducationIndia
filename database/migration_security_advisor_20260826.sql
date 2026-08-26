-- ============================================================================
-- Security Advisor hardening — 2026-08-26
--
-- Closes two live findings surfaced by the Supabase Security Advisor and a
-- follow-up audit of the running database:
--
--   1. public.alembic_version had RLS disabled and full DML granted to the
--      `anon` role. This is the table the advisor flagged as
--      `rls_disabled_in_public`. Alembic's bookkeeping table should never
--      have been reachable from the PostgREST-exposed roles at all.
--
--   2. public.v_paper_health was created without `security_invoker`. A view
--      owned by `postgres` runs with the OWNER's privileges by default, so
--      it bypasses RLS on every table it reads. Combined with the `anon`
--      grant, that let unauthenticated callers read per-exam defect counts
--      for every paper, including unpublished ones.
--
-- Both fixes pair ENABLE RLS / security_invoker with an explicit REVOKE, so
-- the objects stay closed even if a future default grant re-opens them.
-- Idempotent: safe to re-run.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. alembic_version — migration bookkeeping, never client-facing.
-- ---------------------------------------------------------------------------
-- The table is owned by `postgres` and the backend connects as `postgres`,
-- which bypasses RLS unless FORCE is set. Alembic keeps working after this.
ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;

-- No policies are created on purpose: with RLS on and zero policies, every
-- non-owner role is denied by default. That is the intended end state here.
REVOKE ALL ON public.alembic_version FROM anon, authenticated;

-- ---------------------------------------------------------------------------
-- 2. v_paper_health — admin-facing paper QA view.
-- ---------------------------------------------------------------------------
-- security_invoker makes the view honour the CALLER's RLS instead of the
-- owner's, matching the other three application views.
ALTER VIEW public.v_paper_health SET (security_invoker = true);

-- The view is consumed by the admin API over the `postgres` connection, so
-- the PostgREST roles need no access to it whatsoever.
REVOKE ALL ON public.v_paper_health FROM anon, authenticated;

-- ---------------------------------------------------------------------------
-- 3. Answer-key exposure — HIGHEST SEVERITY finding of this audit.
-- ---------------------------------------------------------------------------
-- Not reported by the Supabase Advisor (these tables DO have RLS enabled, so
-- the automated check passes), but found by auditing the policies themselves:
--
--   options."Anyone reads options"                USING (true)
--   questions."Anyone reads questions for active exams"
--                                                 USING (exam is_active)
--
-- RLS is ROW-level, not column-level. Those policies therefore expose every
-- column of the matching rows — including options.is_correct,
-- questions.correct_option, explanation_en/mr and hint_en/mr. Verified against
-- the live database: the `anon` role could read 410 correct answers for
-- currently-active exams. v_exam_answers (documented "post-exam review only")
-- was likewise granted to anon.
--
-- Impact: anyone holding the public VITE_SUPABASE_ANON_KEY — which ships in
-- the frontend bundle by design — could extract the full answer key for a
-- live paper before sitting it. This breaks the ADR-012 security boundary at
-- the database layer, underneath the application-level protections
-- (v_exam_questions / QuestionDeliverySchema) that were enforcing it.
--
-- Fix: revoke the table grants rather than rewrite the policies.
--   * A `USING (true)` policy is inert if the role cannot SELECT the table.
--   * Avoids re-deriving which rows a rewritten policy would expose, and so
--     cannot accidentally break live exam delivery.
--   * The policies are intentionally LEFT IN PLACE as defence-in-depth.
--
-- Safe because no client talks to PostgREST: the frontend uses supabase-js
-- exclusively for auth (supabase.auth.*) and routes all data through the
-- FastAPI backend, which connects as `postgres` (the table owner) and is
-- unaffected by both grants and RLS.
REVOKE ALL ON public.questions         FROM anon, authenticated;
REVOKE ALL ON public.options           FROM anon, authenticated;
REVOKE ALL ON public.question_contexts FROM anon, authenticated;
REVOKE ALL ON public.v_exam_answers    FROM anon, authenticated;

-- question_contexts holds no answer data (passage/figure stimulus only), but
-- migration 0006 drops its public-read policy and revokes only SELECT, leaving
-- INSERT/UPDATE/DELETE grants behind. RLS blocks those writes, but the grants
-- are needless surface, so they are revoked here too.
--
-- ORDERING: this revision MUST run after 0006. Lines 110-112 of 0006 re-GRANT
-- SELECT/INSERT/UPDATE/DELETE on questions/options/question_contexts to
-- `authenticated`; running 0009 first would let 0006 undo it. Applying in
-- chain order leaves the grants stripped, which is the intended end state.
