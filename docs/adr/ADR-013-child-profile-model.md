# ADR-013: Child Profile Model

**Status:** Accepted
**Date:** 2026-02
**Replaces:** ADR-009 (Parent-Student Auth — join table)

---

## Context

ADR-009 designed students as full Supabase Auth accounts linked to
parents via `parent_student_links`. After user research on the target
demographic (Maharashtra parents preparing 5th/8th std children for
MSCE scholarship exam), this design has three problems:

1. **Minor email accounts** — Students aged 10-14 don't reliably
   manage their own email. Parents end up registering on the child's
   behalf, then forgetting the credentials.

2. **Device sharing** — This demographic uses one shared family tablet
   or phone. A separate student login creates unnecessary switching.

3. **Complexity** — Two-account model (parent + student) with a link
   table is harder to support when parents contact help desk.

The target workflow is:
```
Parent logs in → selects child → hands device to child
→ child takes exam → parent sees result
```
This doesn't need a student account. It needs a child profile.

---

## Decision

Replace student Supabase Auth accounts and `parent_student_links`
with a lightweight `child_profiles` table owned entirely by the parent.

**Child profile = a DB row, not an Auth account.**
No email. No password. No Supabase Auth entry.
Parent creates it in under 10 seconds (name + class).

---

## New Table: child_profiles

```sql
CREATE TABLE child_profiles (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id     UUID NOT NULL REFERENCES user_profiles(id)
                  ON DELETE CASCADE,
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
```

---

## Modified Table: attempts

```sql
-- Add child_profile_id alongside existing student_id
-- student_id kept temporarily, nulled out going forward
ALTER TABLE attempts
    ADD COLUMN child_profile_id UUID
    REFERENCES child_profiles(id);
```

All new attempts use `child_profile_id`.
`student_id` column kept for backwards compat, set to NULL on new rows.

---

## Removed

- `parent_student_links` table — left in DB but no longer used.
  Dropped manually after V2 is stable.
- Student Supabase Auth account creation — removed from registration.
- `user_profiles` rows with `role = 'student'` — no longer created.

---

## RLS Policies

```sql
-- Parent sees only their own children
CREATE POLICY "parent_owns_child_profiles" ON child_profiles
    FOR ALL USING (parent_id = auth.uid() OR is_admin());
```

Attempts RLS follows child ownership:
```sql
-- Parent can see attempts for their child profiles
CREATE POLICY "parent_sees_child_attempts" ON attempts
    FOR SELECT USING (
        child_profile_id IN (
            SELECT id FROM child_profiles
            WHERE parent_id = auth.uid()
        )
        OR is_admin()
    );
```

---

## Access Pattern: Start Exam for Child

```
Parent Dashboard
  → Click "Start Exam for Rohan"
  → POST /api/attempts/start
    { exam_id: 1, child_profile_id: "uuid-rohan" }
  → Attempt created with child_profile_id = Rohan's UUID
  → Page hands to child
  → Child takes exam
  → Parent sees result under Rohan's profile
```

---

## Consequences

**Positive:**
- No minor email accounts required
- One login, one account — parent owns everything
- Child creation takes 10 seconds
- Simpler support — one account to look up
- Data model is cleaner (ownership explicit, not via join)

**Negative:**
- Child cannot independently access their own data
- If two parents want to share access (divorced family),
  one parent must share login — acceptable for now
- Child cannot practice at school without parent login

**Accepted trade-offs:**
Target age group (10-14) and usage pattern (home, one device,
parent-supervised) make these trade-offs acceptable.
These edge cases are deferred to a future ADR if needed.

---

## Modules Affected

| Module   | Change                                      |
|----------|---------------------------------------------|
| user     | parent_schemas, repo, service rewritten     |
| attempt  | child_profile_id added to start_exam()      |
| parent FE| store + CreateChildModal rewritten          |
| analysis | no change (reads from attempts)             |
| question | no change                                   |
| catalog  | no change                                   |
| auth     | no change                                   |
