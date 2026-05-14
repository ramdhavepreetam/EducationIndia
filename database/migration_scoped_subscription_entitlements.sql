-- Scoped subscription entitlements
-- Adds flexible plan-to-catalog access rules while preserving existing Standard Access users.

ALTER TABLE public.subscription_plans
    ADD COLUMN IF NOT EXISTS description_en TEXT,
    ADD COLUMN IF NOT EXISTS description_mr TEXT,
    ADD COLUMN IF NOT EXISTS display_order INT DEFAULT 1;

UPDATE public.subscription_plans
SET
    description_en = COALESCE(description_en, 'Access to the exams covered by this plan.'),
    display_order = COALESCE(display_order, id)
WHERE description_en IS NULL OR display_order IS NULL;

CREATE TABLE IF NOT EXISTS public.subscription_plan_entitlements (
    id          SERIAL PRIMARY KEY,
    plan_id     INT NOT NULL REFERENCES public.subscription_plans(id) ON DELETE CASCADE,
    scope_type  VARCHAR(20) NOT NULL CHECK (
        scope_type IN ('all', 'board', 'category', 'std_class', 'event', 'exam')
    ),
    board_id    INT REFERENCES public.exam_boards(id) ON DELETE CASCADE,
    category_id INT REFERENCES public.exam_categories(id) ON DELETE CASCADE,
    std_class   SMALLINT,
    event_id    INT REFERENCES public.exam_events(id) ON DELETE CASCADE,
    exam_id     INT REFERENCES public.exams(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ DEFAULT now(),
    CHECK (
        (scope_type = 'all'
            AND board_id IS NULL AND category_id IS NULL AND std_class IS NULL
            AND event_id IS NULL AND exam_id IS NULL)
        OR (scope_type = 'board' AND board_id IS NOT NULL)
        OR (scope_type = 'category' AND category_id IS NOT NULL)
        OR (scope_type = 'std_class' AND std_class IS NOT NULL)
        OR (scope_type = 'event' AND event_id IS NOT NULL)
        OR (scope_type = 'exam' AND exam_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_subscription_plan_entitlements_plan
    ON public.subscription_plan_entitlements(plan_id);
CREATE INDEX IF NOT EXISTS idx_subscription_plan_entitlements_scope
    ON public.subscription_plan_entitlements(scope_type, board_id, category_id, std_class, event_id, exam_id);
CREATE INDEX IF NOT EXISTS idx_subscription_plans_active_order
    ON public.subscription_plans(is_active, display_order, id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_parent_active
    ON public.subscriptions(parent_id, status, expires_at) WHERE status = 'active';

INSERT INTO public.subscription_plan_entitlements (plan_id, scope_type)
SELECT sp.id, 'all'
FROM public.subscription_plans sp
WHERE sp.name = 'Standard Access'
  AND NOT EXISTS (
      SELECT 1
      FROM public.subscription_plan_entitlements spe
      WHERE spe.plan_id = sp.id
  );

ALTER TABLE public.subscription_plan_entitlements ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone reads active plan entitlements" ON public.subscription_plan_entitlements;
CREATE POLICY "Anyone reads active plan entitlements"
ON public.subscription_plan_entitlements
FOR SELECT
USING (
    EXISTS (
        SELECT 1
        FROM public.subscription_plans sp
        WHERE sp.id = public.subscription_plan_entitlements.plan_id
          AND sp.is_active = true
    )
);

DROP POLICY IF EXISTS "Admins manage plan entitlements" ON public.subscription_plan_entitlements;
CREATE POLICY "Admins manage plan entitlements"
ON public.subscription_plan_entitlements
FOR ALL
USING (is_admin())
WITH CHECK (is_admin());
