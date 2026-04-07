# ADR-009: Parent-Student Authorization Model

**Date:** 2025-02-21
**Status:** Superseded by ADR-013
**Decider:** Preetam
**Modules Affected:** user, auth, attempt, analysis, parent dashboard

---

## Context

ScholarPath has a parent dashboard requirement: parents must see what their
children are doing, how they're performing, their attempt history, and what
topics need focus. This is a fundamentally different access pattern from the
student — a parent must see data owned by another user. Standard RLS "users
see their own data" doesn't cover this case. Additionally, one parent may
monitor multiple children, and one child may have two parents (both wanting
access). The solution must be secure — a student must never see another
student's data, even with a crafted request.

---

## Decision

We will use a parent_student_links join table as the authority for cross-user
data access. RLS policies use a parent_can_see_student(student_id) helper
function that queries this table. Parents are a separate role in user_profiles.
A parent account cannot also be a student account (separate auth users).
Links are created by admin or by parent self-service with student verification.

---

## Alternatives Considered

### Option 1: Parent as a property of student profile
student.parent_id UUID → single parent only, stored on student row.
- Pro: Simple — one column
- Con: Only one parent per student (not realistic — both parents may want access)
- Con: Student record must be updated to add/change parent (wrong ownership)

### Option 2: Same account, role switching
One account can be both student and parent with a role switch.
- Pro: Single login for parent who also took same exam
- Con: Confuses analytics (is this a student attempt or parent testing?)
- Con: Complex RLS — same auth.uid() but different access based on current role
- Con: Children (age 10-14) should not share accounts with parents

### Option 3: parent_student_links join table ← CHOSEN
Separate accounts, explicit link table, RLS helper function.
- Pro: Clear separation — parent account ≠ student account
- Pro: One parent can link to multiple children
- Pro: One student can have multiple parents monitoring them
- Pro: Link can be deactivated without deleting either account
- Pro: RLS helper is a single trusted function, easy to audit
- Con: Requires parent to create account separately and link to child

---

## Consequences

### Positive
- Parent dashboard reads are fast — parent_student_links is a small table
- Adding/removing parent access is instant (flip is_active on link row)
- RLS enforced at DB level — no application-level security checks needed
- Admin can see and manage all parent-child relationships

### Negative
- Parent must create their own account separately from student
- Link creation flow requires UX work (how does parent find/link to child?)
- Two separate logins for a family (parent + child)

### Neutral
- parent_can_see_student() helper used in RLS policies for: attempts, responses,
  user_profiles, exam_assignments
- Parents have READ-ONLY access to child data — no write permissions

---

## Module Impact

```
user/models.py             → parent_student_links table
user/service.py            → link_parent_to_student(), get_parent_children()
user/router.py             → POST /api/users/link-child, GET /api/users/my-children
auth/dependencies.py       → require_role() covers 'parent' role
database migration         → parent_can_see_student() RLS helper function
parent module (frontend)   → reads attempt + analysis data for linked children
RLS policies               → updated on attempts, responses, user_profiles tables
```

---

## Implementation Notes

Link creation flow options:
```
Option A: Admin creates links manually in admin panel
  → Simple for launch, admin controls who can monitor whom
  
Option B: Parent enters child's registered email to request link
  → Child (or admin) approves the link request
  → More self-service but requires notification system
  
Recommendation: Start with Option A (admin-managed), 
add Option B after notification system is in place.
```

RLS helper (already in migration SQL):
```sql
CREATE OR REPLACE FUNCTION parent_can_see_student(p_student_id UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM parent_student_links
        WHERE parent_id = auth.uid()
        AND student_id = p_student_id
        AND is_active = true
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;
```

Parent dashboard data access pattern:
```python
# FastAPI endpoint for parent dashboard
@router.get("/my-children/attempts")
async def get_children_attempts(user: UserIdentity = Depends(verify_token)):
    if user.role != "parent":
        raise HTTPException(403)
    # RLS handles the rest — parent only sees linked children's attempts
    children = await user_service.get_parent_children(user.id)
    return await attempt_service.get_attempts_for_students(
        [child.id for child in children]
    )
```

---

## Review Trigger

Revisit when adding teacher role — teachers may need to see all students
in their class, requiring a different access pattern (class_id based, not
individual links). Revisit when self-service linking is requested by users.
