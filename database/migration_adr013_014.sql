-- ScholarPath ADR-013 + ADR-014 Migration
-- Creates: child_profiles, app_settings, subscription_plans, subscriptions, payments
-- Creates: parent_has_active_subscription() function
-- Adds: child_profile_id column to attempts table
-- Run in Supabase SQL Editor

-- ══════════════════════════════════════════════════════════════════════════════
-- ADR-013: Child Profiles (replaces parent_student_links for new accounts)
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS child_profiles (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id     UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    std_class     SMALLINT NOT NULL CHECK (std_class IN (5, 8)),
    medium        medium_type DEFAULT 'english',
    school_name   TEXT,
    district      TEXT,
    avatar_color  VARCHAR(7) DEFAULT '#3B82F6',
    is_active     BOOLEAN DEFAULT true,
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_child_profiles_parent_id ON child_profiles(parent_id);

-- RLS: parent owns their child profiles
ALTER TABLE child_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "parent_owns_child_profiles" ON child_profiles
    FOR ALL USING (parent_id = auth.uid() OR is_admin());

-- ══════════════════════════════════════════════════════════════════════════════
-- ADR-013: Add child_profile_id to attempts
-- ══════════════════════════════════════════════════════════════════════════════

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'attempts' AND column_name = 'child_profile_id'
    ) THEN
        ALTER TABLE attempts ADD COLUMN child_profile_id UUID REFERENCES child_profiles(id);
        CREATE INDEX idx_attempts_child_profile_id ON attempts(child_profile_id);
    END IF;
END $$;

-- ══════════════════════════════════════════════════════════════════════════════
-- ADR-014: App Settings (admin-configurable key-value store)
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS app_settings (
    key         VARCHAR(100) PRIMARY KEY,
    value       TEXT NOT NULL,
    type        VARCHAR(20) DEFAULT 'string',
    label       TEXT,
    updated_at  TIMESTAMPTZ DEFAULT now(),
    updated_by  UUID REFERENCES user_profiles(id)
);

-- Seed default settings (ADR-014)
INSERT INTO app_settings (key, value, type, label) VALUES
    ('payment_amount_inr',     '499',         'int',     'Payment Amount (INR)'),
    ('access_duration_months', '5',           'int',     'Access Duration (Months)'),
    ('free_tier_exam_id',      '1',           'int',     'Free Tier Exam ID'),
    ('free_tier_max_attempts', '3',           'int',     'Free Tier Max Attempts'),
    ('razorpay_key_id',        '',            'string',  'Razorpay Key ID (Public)'),
    ('app_name',               'ScholarPath', 'string',  'App Name'),
    ('support_email',          '',            'string',  'Support Email'),
    ('maintenance_mode',       'false',       'boolean', 'Maintenance Mode'),
    ('new_registrations',      'true',        'boolean', 'Allow New Registrations')
ON CONFLICT (key) DO NOTHING;

-- ══════════════════════════════════════════════════════════════════════════════
-- ADR-014: Subscription Plans
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS subscription_plans (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    duration_months SMALLINT DEFAULT 5,
    price_inr       INT NOT NULL,
    max_children    INT DEFAULT 999,
    features        JSONB DEFAULT '{}',
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Seed default plan
INSERT INTO subscription_plans (name, duration_months, price_inr, features)
SELECT 'Standard Access', 5, 499, '{"all_exams": true, "full_analysis": true, "pdf_download": true}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM subscription_plans WHERE name = 'Standard Access');

-- ══════════════════════════════════════════════════════════════════════════════
-- ADR-014: Subscriptions (per-parent)
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS subscriptions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id           UUID NOT NULL REFERENCES user_profiles(id),
    plan_id             INT REFERENCES subscription_plans(id),
    status              VARCHAR(20) DEFAULT 'pending'
                        CHECK (status IN ('pending','active','expired','cancelled')),
    started_at          TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ,
    razorpay_order_id   TEXT UNIQUE,
    razorpay_payment_id TEXT,
    amount_paid_inr     INT,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_parent_id ON subscriptions(parent_id);

-- ══════════════════════════════════════════════════════════════════════════════
-- ADR-014: Payments (per-transaction)
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS payments (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id       UUID REFERENCES subscriptions(id),
    parent_id             UUID NOT NULL REFERENCES user_profiles(id),
    amount_inr            INT NOT NULL,
    currency              VARCHAR(5) DEFAULT 'INR',
    razorpay_order_id     TEXT,
    razorpay_payment_id   TEXT,
    razorpay_signature    TEXT,
    status                VARCHAR(20) DEFAULT 'created'
                          CHECK (status IN ('created','captured','failed','refunded')),
    paid_at               TIMESTAMPTZ,
    failure_reason        TEXT,
    created_at            TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_payments_parent_id ON payments(parent_id);

-- ══════════════════════════════════════════════════════════════════════════════
-- ADR-014: Helper function for access_control.py
-- ══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION parent_has_active_subscription(p_parent_id UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM subscriptions
        WHERE parent_id = p_parent_id
          AND status = 'active'
          AND expires_at > now()
    );
$$ LANGUAGE sql STABLE;
