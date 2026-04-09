# Multi-Test Support Design
**Date:** 2026-04-09
**Status:** Approved
**Scope:** ScholarPath — 5th & 8th standard MSCE exam portal

---

## Problem Statement

Currently the platform has a single exam event ("MSCE 5th Std 2025") containing Paper I and Paper II. The goal is to support multiple test sets — each test is a year's exam set consisting of Paper I and Paper II. Students should see all tests assigned to their grade and be able to take each paper independently.

---

## Approach

Use the existing `exam_events` table as the "Test" concept. No schema changes required. Each `exam_event` represents one test set. Admin creates new events with a custom title. Students are auto-assigned to all active exams matching their grade (`std_class`).

### Data Hierarchy (unchanged)
```
exam_board (MSCE Maharashtra)
  └── exam_category (Pre-Upper Primary Scholarship)
        └── exam_event  ← "Test" (custom title, e.g. "MSCE 2024 Practice Set")
              ├── exam (Paper I — paper_code='501', set_code=year e.g. '2024')
              └── exam (Paper II — paper_code='502', set_code=year e.g. '2024')
```

---

## Section 1: Data Model

No schema changes. All required tables already exist:

- `exam_events` — represents a test (custom title, std_class, year)
- `exams` — individual papers under an event
- `exam_assignments` — links students to specific exams with attempt tracking

### Paper Code Strategy

The `exams` table has `UNIQUE(paper_code, set_code)`. The existing seeded exams use `paper_code='501'/'502'` and `set_code='A'`. To avoid collisions when creating new tests, **`set_code` is set to the 4-digit year** (e.g. `'2024'`, `'2023'`). This makes every `(paper_code, set_code)` pair unique across test sets.

| Test | Paper | paper_code | set_code |
|------|-------|------------|----------|
| MSCE 2025 | Paper I | `501` | `2025` |
| MSCE 2025 | Paper II | `502` | `2025` |
| MSCE 2024 | Paper I | `501` | `2024` |
| MSCE 2024 | Paper II | `502` | `2024` |

The existing seeded exams have `set_code='A'` — these will be updated to `'2025'` as part of this implementation to maintain consistency.

**New backend endpoints (admin only):**

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/admin/catalog/events` | Create a new exam_event (test) |
| `POST` | `/api/admin/catalog/events/{id}/exams` | Create Paper I or II under an event |
| `GET`  | `/api/admin/catalog/events` | List all events with grade + paper status |

---

## Section 2: Auto-Assignment by Grade

When a student's `std_class` is saved, the system automatically creates `exam_assignments` rows for every active exam matching that grade.

### Guard: NULL std_class

Auto-assignment fires **only when `std_class` is present and has a value of 5 or 8**. If `std_class` is NULL (e.g. parent role, or partial profile update that omits the field), auto-assignment is skipped silently. Since `update_my_profile()` uses `exclude_unset=True`, a request that does not include `std_class` will never trigger auto-assignment.

### Three Triggers

1. **Student completes onboarding** — `std_class` is set (required) → auto-assign all active exams for that grade
2. **Student changes grade in profile** — `std_class` changes to a new valid value → set `is_active=false` on all previous auto-assignments (where `assigned_by IS NULL`) → upsert assignments for the new grade's active exams
3. **Admin publishes a new paper** — after `exam.is_active` becomes `true` → auto-assign to all students where `user_profiles.std_class` matches the event's `std_class`

### Assignment Record Created
```
assignment_type  = 'practice'
assigned_by      = NULL          (system-assigned)
max_attempts     = 10
valid_from/until = NULL          (no expiry)
is_active        = true
```

### Upsert Strategy (Grade Change Safe)

The `bulk_create_assignments` method uses a conditional upsert:

```sql
INSERT INTO exam_assignments (exam_id, student_id, assignment_type, assigned_by, max_attempts, is_active, ...)
VALUES (...)
ON CONFLICT (exam_id, student_id)
DO UPDATE SET is_active = true
WHERE exam_assignments.assigned_by IS NULL
```

**Behaviour by case:**
- First assignment → inserts cleanly
- Re-publishing same exam → idempotent (existing auto row re-activated)
- Student returning to previous grade → deactivated auto-row re-activated with `is_active=true`
- Manually assigned row exists for the same `(exam_id, student_id)` → the `WHERE` fails, PostgreSQL does nothing (no insert, no update). This is intentional: the student already has access via their manual assignment; no separate auto-assignment row is needed. `UNIQUE(exam_id, student_id)` means one row per pair.

Note: `exam_assignments` has **no `updated_at` column** in the schema — do not include it in any INSERT or UPDATE.

### Grade Change — Deactivation Step

When `std_class` changes, the service must deactivate the student's previous grade's auto-assignments before creating new ones:

- New method: `attempt_repository.deactivate_auto_assignments_for_student(student_id, db)` — runs `UPDATE exam_assignments SET is_active=false WHERE student_id=:sid AND assigned_by IS NULL`
- Called from `user_service.auto_assign_exams_for_grade()` before bulk-inserting new assignments
- Only deactivates auto-assigned rows (`assigned_by IS NULL`); teacher-assigned rows are left untouched

### Module Ownership

`bulk_create_assignments(rows)` and `deactivate_auto_assignments_for_student(student_id, db)` live in `attempt/repository.py` — the attempt module owns `exam_assignments`.

Cross-module access pattern: user and catalog services import and call `attempt_repository` (the singleton) directly — the same pattern used by the parent module, which calls raw SQL via `text()` to access attempt data. Calling a repository singleton from another module's service is the established cross-module data access pattern in this project. No attempt ORM models are imported; only the public repository singleton is used.

- `user_service.auto_assign_exams_for_grade(student_id, std_class, db)` — calls `attempt_repository.bulk_create_assignments()` and `attempt_repository.deactivate_auto_assignments_for_student()`
- `catalog_service.auto_assign_exam_to_grade(exam_id, std_class, db)` — calls `attempt_repository.bulk_create_assignments()`

---

## Section 3: Student Dashboard Experience

### Single "Your Tests" Section

Students see all tests assigned to them, grouped by exam_event. No separate "Available Practice" vs "Assigned" split — all exams come through assignments (auto or manual).

```
─── Your Tests (Class 5) ───────────────────────────
┌─────────────────────────────────────────────────┐
│  MSCE 2025 Practice Set                    [▼]  │
├─────────────────────────────────────────────────┤
│  📄 Paper I    8/10 attempts left  [Start →]    │
│  📄 Paper II   10/10 attempts left [Start →]    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  MSCE 2024 Practice Set                    [▼]  │
├─────────────────────────────────────────────────┤
│  📄 Paper I    10/10 attempts left [Start →]    │
│  📄 Paper II   9/10 attempts left  [Start →]    │
└─────────────────────────────────────────────────┘
```

### Paper Button States

| Condition | Button |
|-----------|--------|
| No ongoing attempt, attempts remaining | `Start →` |
| Ongoing attempt exists | `Resume →` |
| `attempts_used >= max_attempts` | `Completed (10/10)` — disabled |
| Exam locked (free tier) | `🔒 Upgrade` |
| Teacher-assigned with due date | `Start →` + due date badge |

### Manually Assigned Tests (by teacher/admin)
Show a `[ASSIGNED BY TEACHER]` badge and display due date + remaining attempts prominently.

### API Response Schema Change (Breaking Change)

`GET /api/dashboard/student` currently returns `available_exams: List[ExamSummaryResponse]`. This changes to `List[ExamWithAssignmentResponse]`.

**New schema `ExamWithAssignmentResponse`** (extends `ExamSummaryResponse`, adds):
```
event_title       TEXT        — used for frontend grouping
event_year        SMALLINT    — used for sorting
std_class         SMALLINT    — grade this exam belongs to
attempts_used     SMALLINT    — from exam_assignments
max_attempts      SMALLINT    — from exam_assignments
assignment_id     INT         — needed for StartAttemptRequest (see Section 4)
valid_until       TIMESTAMPTZ — NULL for auto-assigned practice
assignment_type   TEXT        — 'practice' | 'assigned' | 'mock_test'
assigned_by_name  TEXT        — NULL for auto-assigned; teacher name for manual
```

`ExamSummaryResponse` used in other catalog endpoints is **not modified** — the dashboard uses the new extended type only.

### Frontend Changes
- `StudentDashboardPage.jsx` — group `available_exams` by `event_title`, sort by `event_year DESC`
- Replace `AvailableExamCard` with new `TestGroupCard` component — expandable group showing Paper I + Paper II rows
- New `PaperRow` sub-component — paper title, attempts remaining, button state, passes `assignment_id` to start URL
- First test group expanded by default; rest collapsed

---

## Section 4: Exam Taking Process

### Two Attempt Flows

The `attempt` module already supports two flows:

| Flow | Who | `attempts.student_id` | `attempts.child_profile_id` |
|------|-----|----------------------|------------------------------|
| Direct student | Student with own login | student's `user_profiles.id` | NULL |
| Parent-for-child | Parent acting for a child profile | NULL | child's `child_profiles.id` |

**Current bug (pre-existing):** `create_attempt()` currently hardcodes `student_id=None` even for direct students. The DB trigger `increment_attempts_used` fires on `WHERE exam_id=NEW.exam_id AND student_id=NEW.student_id` — so it currently never fires for direct students (NULL matches nothing).

**This feature requires fixing this bug as a prerequisite.** Direct student attempts must set `attempts.student_id = identity.id` (from JWT).

### `StartAttemptRequest` Schema Change

Currently `StartAttemptRequest.child_profile_id: UUID` is required. Change to optional:

```python
child_profile_id: Optional[UUID] = None   # None for direct student flow
```

### Resolved Student ID

In `start_exam()`, resolve the effective student ID early:

```python
effective_student_id = request.child_profile_id if request.child_profile_id else identity.id
```

All downstream calls in `start_exam()` use `effective_student_id`:
- `_validate_assignment(db, request.assignment_id, effective_student_id)` — assignment row uses `student_id = effective_student_id`
- `attempt_repository.get_ongoing_attempt(db, effective_student_id, request.exam_id)`
- `attempt_repository.get_attempt_number(db, effective_student_id, request.exam_id)`
- `attempt_repository.create_attempt(db, student_id=identity.id if not request.child_profile_id else None, child_profile_id=request.child_profile_id, ...)`

### Repository Methods: Dual-Path Query

`get_ongoing_attempt` and `get_attempt_number` currently filter on `Attempt.child_profile_id`. They must handle both flows:

```python
# Pseudocode for both methods:
if child_profile_id is not None:
    filter = Attempt.child_profile_id == child_profile_id
else:
    filter = (Attempt.student_id == student_id) & (Attempt.child_profile_id == None)
```

This ensures direct-student attempts are correctly found (not creating duplicate ongoing attempts) and attempt numbering is correct.

### Full Flow (Direct Student)
```
Student clicks [Start] on Paper I
        ↓
POST /api/attempts/start  { exam_id, assignment_id }
  1. child_profile_id is None → effective_student_id = identity.id
  2. Validate assignment: exam_assignments where student_id=identity.id + exam_id + is_active=true
  3. Check attempts_used < max_attempts → else 409
  4. Check no ongoing attempt → else return existing (resume)
  5. Create attempt (student_id=identity.id, child_profile_id=None, assignment_id=assignment_id)
  6. Return 75 questions via v_exam_questions (no correct_option)
        ↓
Student takes exam (timer, question palette, autosave every 30s)
        ↓
POST /api/attempts/{id}/submit
  1. Score computed → stored in section_scores, topic_scores, time_analysis
  2. attempt.status → 'submitted'
  3. DB trigger fires: attempts.student_id=identity.id → increments exam_assignments.attempts_used
        ↓
Result page: full analysis, wrong answers, topic breakdown, PDF export
```

### DB Trigger Behaviour

The `increment_attempts_used` trigger increments via `(exam_id, student_id)`:

```sql
UPDATE exam_assignments
SET attempts_used = attempts_used + 1
WHERE exam_id = NEW.exam_id AND student_id = NEW.student_id;
```

Once `student_id` is correctly set on the attempt row, the trigger fires and `exam_assignments.attempts_used` is incremented. `assignment_id` in the attempt row is for reporting/auditing only — it has no effect on the trigger.

### Confirm `start_exam` handles `assigned_by=NULL`

The assignment validation checks `is_active` and `attempts_used`. It does not check `assigned_by`. Auto-assigned rows (`assigned_by=NULL`) are handled identically to manually assigned rows — no code change needed for this.

---

## Section 5: Admin Experience

### New Page: Create Test (`/admin/tests/new`)

Three-step workflow:

**Step 1 — Test Details**
- Custom title (e.g. "MSCE 2024 Practice Set")
- Grade: Class 5 or Class 8
- Year (4-digit, e.g. 2024 — used as set_code and for sorting)

**Step 2 — Papers (auto-created)**
System creates:
- `exam_event` row with the title + grade + year
- 2 `exam` rows: Paper I (`paper_code='501'`, `set_code=year`) and Paper II (`paper_code='502'`, `set_code=year`), both `is_active=false`
- 4 `section` rows (Sections I+II for each paper) cloned from existing structure
- 26 `topic` rows cloned from existing structure

**Step 3 — Import Questions**
Admin is directed to Question Manager to import questions per paper. Papers show as Draft until 75 questions are loaded and published.

### Updated Exam Publisher Page

Shows tests grouped by event with grade label:

```
MSCE 2025 Practice Set — Class 5
  Paper I    75/75 ✅  [Live]   [Unpublish]
  Paper II   60/75 ⚠️  [Draft]  [Publish — needs 15 more Qs]

MSCE 2024 Practice Set — Class 5
  Paper I    75/75 ✅  [Live]   [Unpublish]
  Paper II   75/75 ✅  [Live]   [Unpublish]
```

### Auto-Assign Confirmation on Publish

When admin publishes a paper, backend returns count of students auto-assigned:

```json
{
  "exam_id": 5,
  "is_active": true,
  "auto_assigned_count": 47
}
```

Admin sees: `✅ Paper I published. Auto-assigned to 47 Class 5 students.`

---

## Module Impact Summary

| Module | Change Type | What Changes |
|--------|-------------|--------------|
| `catalog` (backend) | New endpoints | `POST /events`, `POST /events/{id}/exams`, `GET /events` |
| `catalog` (backend) | Updated | `publish_exam()` triggers `auto_assign_exam_to_grade()`; returns `auto_assigned_count` |
| `user` (backend) | Updated | `complete_onboarding()` + `update_my_profile()` trigger `auto_assign_exams_for_grade()` when std_class is 5 or 8 |
| `attempt` (backend) | Bug fix + new methods | Make `StartAttemptRequest.child_profile_id` Optional; resolve `effective_student_id` in `start_exam()`; fix `create_attempt()` to set `student_id=identity.id` for direct flow; update `get_ongoing_attempt()` and `get_attempt_number()` for dual-path query; add `bulk_create_assignments()` and `deactivate_auto_assignments_for_student()` to attempt repository |
| `admin` (frontend) | New page | `CreateTestPage` at `/admin/tests/new` |
| `admin` (frontend) | Updated | `ExamPublisherPage` shows grade label + auto-assign count on publish |
| `dashboard` (backend) | Updated | `StudentDashboardResponse.available_exams` type changes to `List[ExamWithAssignmentResponse]` |
| `dashboard` (frontend) | Updated | `StudentDashboardPage` groups exams by test; sorts by event_year DESC |
| `dashboard` (frontend) | New components | `TestGroupCard` (expandable) + `PaperRow` (passes assignment_id) |

---

## Out of Scope

- 8th standard exams (architecture is identical — just different `std_class` value; same code handles it)
- Attempt count reset by admin (future feature)
- Student ability to see other grade's tests (not allowed — assignments are grade-gated)
- Updating the existing seeded exams' `set_code` from `'A'` to `'2025'` is a one-time data fix, not a migration
