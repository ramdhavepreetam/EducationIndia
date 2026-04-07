# ADR-014: Payment and Access Control

**Status:** Accepted
**Date:** 2026-02

---

## Context

ScholarPath needs a monetisation layer. Requirements:

- Gate access to Paper II and full analysis behind payment
- Price and duration must be configurable without code redeploy
- India-first payment (UPI, cards, netbanking)
- Per parent account pricing (all child profiles included)
- Free tier to hook users, paid tier for full access
- Admin controls all settings from a dashboard

---

## Decisions

### 1. Payment Gateway: Razorpay

**Chosen:** Razorpay
**Reason:** India-first, UPI native, widely trusted by Indian parents,
simple webhook setup, INR native, good SDK support.

### 2. Payment Model: One-Time Order

**Chosen:** One-time Razorpay order (not recurring subscription)
**Reason:** 5-month exam prep cycle maps to a one-time purchase.
Indian parents are wary of auto-debit. One-time feels safer and
is easier to explain at ₹499.

### 3. Pricing Scope: Per Parent Account

**Chosen:** ₹499 per parent account covers ALL child profiles.
**Reason:** Easier sell. Two children still ₹499.
Maximises conversion over per-child pricing.

### 4. Price Configurability: app_settings Table

All configurable values live in `app_settings` DB table.
Admin changes value in panel → takes effect immediately.
No code redeploy needed to change price, duration, or free tier limits.

**Configurable settings:**
```
payment_amount_inr       = 499   (shown in ₹ on upgrade page)
access_duration_months   = 5     (how long paid access lasts)
free_tier_exam_id        = 1     (which exam is free)
free_tier_max_attempts   = 3     (attempts before upgrade prompt)
```

### 5. Free Tier Definition

```
Access:   Paper I (exam_id from app_settings) only
Attempts: Max 3 per child (from app_settings)
Result:   Score + grade only
          "Your child scored 118/150 — Good"
Locked:   Topic breakdown, section scores,
          recommendations, PDF download
```

### 6. Paid Tier Definition

```
Access:   All active exams
Attempts: Unlimited
Result:   Full analysis
          Section scores, topic breakdown,
          recommendations, PDF download
Duration: access_duration_months from app_settings
Scope:    All child profiles under the parent account
```

### 7. Expiry Behaviour: Full Lockout

On expiry:
- Past results remain visible (read-only, stored JSONB)
- New exam attempts blocked (except free tier exam + limits)
- Upgrade prompt shown throughout app
- No grace period (keep it simple for V1)

### 8. Access Control: Single Shared Utility

**File:** `backend/app/shared/access_control.py`

Single source of truth. Never duplicated in individual modules.
Every access decision goes through `get_access_context()`.

---

## New Tables

### app_settings

```sql
CREATE TABLE app_settings (
    key         VARCHAR(100) PRIMARY KEY,
    value       TEXT NOT NULL,
    type        VARCHAR(20) DEFAULT 'string',
    label       TEXT,
    updated_at  TIMESTAMPTZ DEFAULT now(),
    updated_by  UUID REFERENCES user_profiles(id)
);

-- Default seed data
INSERT INTO app_settings (key, value, type, label) VALUES
  ('payment_amount_inr',     '499',         'int',     'Payment Amount (INR)'),
  ('access_duration_months', '5',           'int',     'Access Duration (Months)'),
  ('free_tier_exam_id',      '1',           'int',     'Free Tier Exam ID'),
  ('free_tier_max_attempts', '3',           'int',     'Free Tier Max Attempts'),
  ('razorpay_key_id',        '',            'string',  'Razorpay Key ID (Public)'),
  ('app_name',               'ScholarPath', 'string',  'App Name'),
  ('support_email',          '',            'string',  'Support Email'),
  ('maintenance_mode',       'false',       'boolean', 'Maintenance Mode'),
  ('new_registrations',      'true',        'boolean', 'Allow New Registrations');
```

### subscription_plans

```sql
CREATE TABLE subscription_plans (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    duration_months SMALLINT DEFAULT 5,
    price_inr       INT NOT NULL,
    max_children    INT DEFAULT 999,
    features        JSONB DEFAULT '{}',
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### subscriptions

```sql
CREATE TABLE subscriptions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id           UUID NOT NULL REFERENCES user_profiles(id),
    plan_id             INT REFERENCES subscription_plans(id),
    status              VARCHAR(20) DEFAULT 'pending'
                        CHECK (status IN
                          ('pending','active','expired','cancelled')),
    started_at          TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ,
    razorpay_order_id   TEXT UNIQUE,
    razorpay_payment_id TEXT,
    amount_paid_inr     INT,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);
```

### payments

```sql
CREATE TABLE payments (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id       UUID REFERENCES subscriptions(id),
    parent_id             UUID NOT NULL REFERENCES user_profiles(id),
    amount_inr            INT NOT NULL,
    currency              VARCHAR(5) DEFAULT 'INR',
    razorpay_order_id     TEXT,
    razorpay_payment_id   TEXT,
    razorpay_signature    TEXT,
    status                VARCHAR(20) DEFAULT 'created'
                          CHECK (status IN
                            ('created','captured','failed','refunded')),
    paid_at               TIMESTAMPTZ,
    failure_reason        TEXT,
    created_at            TIMESTAMPTZ DEFAULT now()
);
```

---

## Access Control Utility

```python
# backend/app/shared/access_control.py

@dataclass
class AccessContext:
    parent_id:         UUID
    is_paid:           bool
    free_exam_id:      int
    free_max_attempts: int

async def get_access_context(parent_id, db) -> AccessContext:
    """Single DB query. Call once per request."""
    ...

async def can_start_exam(ctx, exam_id, attempt_count, db) -> tuple[bool, str]:
    """Returns (allowed, reason). reason used for upgrade prompt."""
    ...

def can_see_full_analysis(ctx) -> bool:
    """True for paid tier only."""
    ...

def can_download_pdf(ctx) -> bool:
    """True for paid tier only."""
    ...
```

**Rules:**
- `get_access_context()` called ONCE per request
- Result passed as `ctx` to all gate functions
- Never call individual gate functions without ctx
- Never duplicate access logic in individual modules

---

## Payment Flow

```
1. Parent clicks "Upgrade"
   → GET /api/payment/plans  (get current price from DB)

2. Parent clicks "Pay ₹499"
   → POST /api/payment/create-order
   → Backend creates Razorpay order
   → Returns {order_id, amount_paise, key_id}

3. Razorpay checkout opens (browser)
   → Parent pays via UPI/card/netbanking

4. Payment captured
   → Razorpay calls POST /api/payment/webhook (async)
   → Frontend receives handler response with payment_id

5. Frontend calls POST /api/payment/verify
   → Backend verifies HMAC-SHA256 signature
   → If valid: subscription.status = 'active'
               expires_at = now() + duration_months
   → Returns {is_active: true, expires_at: ...}

6. Frontend redirects to /payment/success
   → All papers unlocked
   → Full analysis unlocked
```

---

## Security Rules

```
RAZORPAY_KEY_SECRET  → .env ONLY — never in DB, never in code
RAZORPAY_WEBHOOK_SECRET → .env ONLY

Webhook endpoint:
  → Excluded from JWT auth middleware
  → Signature verified BEFORE processing
  → Idempotent — safe to receive same event twice

Signature verification:
  HMAC = SHA256(order_id + "|" + payment_id, KEY_SECRET)
  Must match razorpay_signature from request
```

---

## Consequences

**Positive:**
- Price change takes 30 seconds (admin panel → save)
- Duration change takes 30 seconds (same)
- Free tier limits configurable without redeploy
- Single access_control.py — no scattered tier logic
- Razorpay handles UPI, which is what Indian parents prefer

**Negative:**
- Webhook must be publicly reachable (fine on Render)
- Razorpay test mode needed during development
- Admin must set RAZORPAY_KEY_SECRET in .env manually
  (cannot be done from admin panel — by design)

---

## Modules Affected

| Module          | Change                                   |
|-----------------|------------------------------------------|
| payment         | new module                               |
| access_control  | new shared utility                       |
| attempt/service | can_start_exam() check added to start    |
| analysis/service| can_see_full_analysis() check added      |
| catalog/service | is_accessible flag added to exam list    |
| admin/router    | settings + subscription endpoints added  |
| question        | no change                                |
| media           | no change                                |
| auth            | no change                                |
