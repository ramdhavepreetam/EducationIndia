-- Security Advisor hardening
-- Applied after the base ScholarPath migrations.

-- Keep extensions outside the exposed public schema.
CREATE SCHEMA IF NOT EXISTS extensions;
ALTER EXTENSION pg_trgm SET SCHEMA extensions;

-- Pin app function search_path so SECURITY DEFINER/helper functions cannot be
-- hijacked through caller-controlled search_path resolution.
ALTER FUNCTION public.handle_new_auth_user() SET search_path = public, auth, pg_temp;
ALTER FUNCTION public.is_admin() SET search_path = public, auth, pg_temp;
ALTER FUNCTION public.is_parent() SET search_path = public, auth, pg_temp;
ALTER FUNCTION public.parent_can_see_student(uuid) SET search_path = public, auth, pg_temp;
ALTER FUNCTION public.parent_has_active_subscription(uuid) SET search_path = public, pg_temp;
ALTER FUNCTION public.update_updated_at() SET search_path = public, pg_temp;
ALTER FUNCTION public.update_updated_at_column() SET search_path = public, pg_temp;
ALTER FUNCTION public.sync_correct_option() SET search_path = public, pg_temp;
ALTER FUNCTION public.update_question_stats_on_submit() SET search_path = public, pg_temp;
ALTER FUNCTION public.increment_attempts_used() SET search_path = public, pg_temp;

-- Make application views run with the caller's privileges/RLS instead of the
-- view owner's privileges.
ALTER VIEW public.v_exam_questions SET (security_invoker = true);
ALTER VIEW public.v_exam_answers SET (security_invoker = true);
ALTER VIEW public.v_student_attempts SET (security_invoker = true);

-- Close public tables that were exposed without RLS.
ALTER TABLE public.exam_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.question_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscription_plans ENABLE ROW LEVEL SECURITY;

-- exam_categories had RLS enabled but no policies, which blocks legitimate
-- direct reads and is flagged by Supabase Advisor.
DROP POLICY IF EXISTS "Anyone reads active exam categories" ON public.exam_categories;
CREATE POLICY "Anyone reads active exam categories"
ON public.exam_categories
FOR SELECT
USING (is_active = true);

DROP POLICY IF EXISTS "Admins manage exam categories" ON public.exam_categories;
CREATE POLICY "Admins manage exam categories"
ON public.exam_categories
FOR ALL
USING (is_admin())
WITH CHECK (is_admin());

-- Stats tables are internal/admin surfaces only.
DROP POLICY IF EXISTS "Admins read exam stats" ON public.exam_stats;
CREATE POLICY "Admins read exam stats"
ON public.exam_stats
FOR SELECT
USING (is_admin());

DROP POLICY IF EXISTS "Admins read question stats" ON public.question_stats;
CREATE POLICY "Admins read question stats"
ON public.question_stats
FOR SELECT
USING (is_admin());

-- Active plan metadata is public for pricing display; writes remain admin-only.
DROP POLICY IF EXISTS "Anyone reads active subscription plans" ON public.subscription_plans;
CREATE POLICY "Anyone reads active subscription plans"
ON public.subscription_plans
FOR SELECT
USING (is_active = true);

DROP POLICY IF EXISTS "Admins manage subscription plans" ON public.subscription_plans;
CREATE POLICY "Admins manage subscription plans"
ON public.subscription_plans
FOR ALL
USING (is_admin())
WITH CHECK (is_admin());
