# Multi-Test Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Support multiple test sets (each with Paper I + Paper II) that are auto-assigned to students by grade when they onboard or when new tests are published.

**Architecture:** `exam_events` rows ARE the "tests". Auto-assignment fires from three triggers (onboarding, grade change, publish). Direct-student attempt flow has a pre-existing bug (`student_id=None`) that must be fixed first — it's a prerequisite for the DB trigger to increment `attempts_used`.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 async + Pydantic v2, React 18 + Zustand + Tailwind CSS

**Spec:** `docs/superpowers/specs/2026-04-09-multi-test-support-design.md`

---

## File Map

### Modified (backend)
- `backend/app/modules/attempt/schemas.py:28` — make `child_profile_id` Optional
- `backend/app/modules/attempt/repository.py:68-98` — fix dual-path queries; add 2 new methods
- `backend/app/modules/attempt/service.py:46-126` — resolve `effective_student_id`
- `backend/app/modules/catalog/schemas.py` — add 3 new request/response schemas
- `backend/app/modules/catalog/repository.py` — add 3 new repo methods
- `backend/app/modules/catalog/service.py` — add 2 new service methods, update `publish_exam`
- `backend/app/modules/catalog/router.py` — add 3 admin event endpoints
- `backend/app/modules/user/service.py:59-80` — call auto-assign after onboarding/grade change
- `backend/app/modules/admin/schemas.py:26-30` — add `ExamWithAssignmentResponse`, update `StudentDashboardResponse`
- `backend/app/modules/admin/router.py:39-119` — rewrite `get_student_dashboard` to join assignments

### Modified (frontend)
- `frontend/src/modules/dashboard/pages/StudentDashboardPage.jsx` — group by event
- `frontend/src/modules/admin/pages/ExamPublisherPage.jsx` — grade label + auto-assign count
- `frontend/src/modules/admin/api/adminApi.js` — add `createTest`, `listAllEvents`
- `frontend/src/modules/admin/store/adminStore.js` — add `createTest`, update `publishExam`
- `frontend/src/App.jsx` — add `/admin/tests/new` route
- `frontend/src/modules/admin/index.js` — export `CreateTestPage`

### Created (frontend)
- `frontend/src/modules/dashboard/components/TestGroupCard.jsx`
- `frontend/src/modules/dashboard/components/PaperRow.jsx`
- `frontend/src/modules/admin/pages/CreateTestPage.jsx`

---

## Task 1: Fix attempt module — direct-student flow prerequisite

**Files:**
- Modify: `backend/app/modules/attempt/schemas.py:28`
- Modify: `backend/app/modules/attempt/repository.py:68-98`
- Modify: `backend/app/modules/attempt/service.py:46-126`
- Test: `backend/tests/test_attempt_direct_student.py` (new)

**Context:** `StartAttemptRequest.child_profile_id` is currently a required `UUID`. The service always passes `student_id=None` to `create_attempt`. The DB trigger `increment_attempts_used` uses `WHERE student_id = NEW.student_id` — so it never fires. This task fixes all three issues.

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_attempt_direct_student.py`:

```python
"""Tests for direct-student attempt flow (no child_profile_id)."""
import pytest
from app.modules.attempt.schemas import StartAttemptRequest
from app.modules.attempt.repository import AttemptRepository

def test_start_attempt_request_child_profile_id_is_optional():
    """child_profile_id should default to None for direct students."""
    req = StartAttemptRequest(exam_id=1, assignment_id=None)
    assert req.child_profile_id is None

def test_start_attempt_request_accepts_child_profile_id():
    """child_profile_id can still be provided for parent-for-child flow."""
    from uuid import uuid4
    req = StartAttemptRequest(exam_id=1, child_profile_id=uuid4())
    assert req.child_profile_id is not None
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/preetam/Documents/AI/scholarpath && \
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/pytest \
  backend/tests/test_attempt_direct_student.py -v
```

Expected: `FAILED` — `StartAttemptRequest` validation error (missing required field).

- [ ] **Step 3: Make `child_profile_id` Optional in schemas.py**

In `backend/app/modules/attempt/schemas.py`, change line 28:

```python
# Before:
child_profile_id: UUID

# After:
child_profile_id: Optional[UUID] = None   # None for direct student flow
```

- [ ] **Step 4: Fix `get_ongoing_attempt` and `get_attempt_number` for dual-path**

In `backend/app/modules/attempt/repository.py`, replace lines 68-98:

```python
async def get_ongoing_attempt(
    self, db: AsyncSession, student_id: UUID, exam_id: int
) -> Attempt | None:
    """
    Return the active ongoing attempt for a student+exam, or None.
    Handles two flows:
      - child_profile_id flow (parent-for-child): filters on child_profile_id
      - direct student flow: filters on student_id with child_profile_id IS NULL
    """
    if student_id is not None:
        # Try direct-student path first
        result = await db.execute(
            select(Attempt).where(
                Attempt.student_id == student_id,
                Attempt.child_profile_id == None,
                Attempt.exam_id == exam_id,
                Attempt.status == "ongoing",
            )
        )
        found = result.scalar_one_or_none()
        if found:
            return found
    # Fall through to child_profile_id path
    result = await db.execute(
        select(Attempt).where(
            Attempt.child_profile_id == student_id,
            Attempt.exam_id == exam_id,
            Attempt.status == "ongoing",
        )
    )
    return result.scalar_one_or_none()

async def get_attempt_number(
    self, db: AsyncSession, student_id: UUID, exam_id: int
) -> int:
    """
    Return the next attempt number for this student+exam.
    Checks both direct-student and child_profile_id rows.
    """
    # Direct-student rows
    r1 = await db.execute(
        select(func.count(Attempt.id)).where(
            Attempt.student_id == student_id,
            Attempt.child_profile_id == None,
            Attempt.exam_id == exam_id,
        )
    )
    # Child-profile rows
    r2 = await db.execute(
        select(func.count(Attempt.id)).where(
            Attempt.child_profile_id == student_id,
            Attempt.exam_id == exam_id,
        )
    )
    count = (r1.scalar_one() or 0) + (r2.scalar_one() or 0)
    return count + 1
```

- [ ] **Step 5: Fix `start_exam` in service.py to resolve effective_student_id**

In `backend/app/modules/attempt/service.py`, replace the `start_exam` method body (lines 68-126):

```python
async def start_exam(
    self,
    db: AsyncSession,
    parent_id: UUID,
    request: StartAttemptRequest,
) -> AttemptStateResponse:
    # 1. Validate exam is active
    exam = await catalog_service.get_active_exam(db, request.exam_id)

    # 1.5 Resolve effective student ID
    # Direct student: child_profile_id is None → use the caller's own identity
    # Parent-for-child: child_profile_id is set → validate ownership
    if request.child_profile_id is not None:
        from app.modules.user.child_repository import ChildRepository
        child_repo = ChildRepository()
        is_owner = await child_repo.validate_ownership(
            request.child_profile_id, parent_id, db
        )
        if not is_owner:
            raise Forbidden("Child profile not found")
        effective_student_id = request.child_profile_id
    else:
        effective_student_id = parent_id   # caller IS the student

    # 1.6 Access control gate (ADR-014)
    from app.shared.access_control import get_access_context, can_start_exam as check_start
    ctx = await get_access_context(parent_id, db)
    allowed, reason = await check_start(
        ctx, request.exam_id, effective_student_id, db
    )
    if not allowed:
        raise Forbidden(reason)

    # 2. Ensure no duplicate ongoing attempt
    existing = await attempt_repository.get_ongoing_attempt(
        db, effective_student_id, request.exam_id
    )
    if existing is not None:
        raise Conflict(
            f"You already have an ongoing attempt (id: {existing.id}) for this exam. "
            "Resume it via GET /api/attempts/{attempt_id}/state or submit it first."
        )

    # 3. Validate assignment if provided
    if request.assignment_id is not None:
        await self._validate_assignment(db, request.assignment_id, effective_student_id)

    # 4. Create attempt — set student_id for direct flow so DB trigger fires
    attempt_number = await attempt_repository.get_attempt_number(
        db, effective_student_id, request.exam_id
    )
    is_direct = request.child_profile_id is None
    attempt = await attempt_repository.create_attempt(
        db,
        child_profile_id=request.child_profile_id,
        student_id=parent_id if is_direct else None,
        exam_id=request.exam_id,
        assignment_id=request.assignment_id,
        attempt_number=attempt_number,
    )

    time_remaining = exam.duration_minutes * 60

    return AttemptStateResponse(
        attempt_id=attempt.id,
        exam_id=attempt.exam_id,
        attempt_number=attempt.attempt_number,
        status=str(attempt.status.value if hasattr(attempt.status, "value") else attempt.status),
        started_at=attempt.started_at,
        time_remaining_seconds=time_remaining,
        responses=[],
    )
```

- [ ] **Step 6: Run tests**

```bash
cd /Users/preetam/Documents/AI/scholarpath && \
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/pytest \
  backend/tests/test_attempt_direct_student.py -v
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/modules/attempt/schemas.py \
        backend/app/modules/attempt/repository.py \
        backend/app/modules/attempt/service.py \
        backend/tests/test_attempt_direct_student.py
git commit -m "fix(attempt): support direct-student flow — make child_profile_id optional, fix student_id on attempts, dual-path repo queries"
```

---

## Task 2: Add bulk assignment methods to attempt repository

**Files:**
- Modify: `backend/app/modules/attempt/repository.py` (add 2 methods at the bottom)
- Test: `backend/tests/test_attempt_direct_student.py` (extend)

**Context:** `attempt_repository` owns `exam_assignments`. These two methods are called by user_service and catalog_service to auto-assign students. They must NOT import any catalog or user models.

- [ ] **Step 1: Write failing tests** (append to `backend/tests/test_attempt_direct_student.py`)

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

@pytest.mark.asyncio
async def test_deactivate_auto_assignments_for_student():
    """deactivate_auto_assignments_for_student runs an UPDATE with assigned_by IS NULL guard."""
    from app.modules.attempt.repository import AttemptRepository
    repo = AttemptRepository()
    db = AsyncMock()
    db.execute = AsyncMock()
    student_id = uuid4()
    await repo.deactivate_auto_assignments_for_student(db, student_id)
    db.execute.assert_awaited_once()
    call_args = str(db.execute.call_args)
    # Verify student_id was passed as parameter
    assert str(student_id) in call_args or "sid" in call_args

@pytest.mark.asyncio
async def test_bulk_create_assignments_calls_execute():
    """bulk_create_assignments executes a PostgreSQL INSERT ... ON CONFLICT upsert."""
    from app.modules.attempt.repository import AttemptRepository
    repo = AttemptRepository()
    db = AsyncMock()
    db.execute = AsyncMock()
    rows = [
        {"exam_id": 1, "student_id": uuid4()},
        {"exam_id": 2, "student_id": uuid4()},
    ]
    await repo.bulk_create_assignments(db, rows)
    assert db.execute.await_count == len(rows)
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/preetam/Documents/AI/scholarpath && \
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/pytest \
  backend/tests/test_attempt_direct_student.py::test_deactivate_auto_assignments_for_student \
  backend/tests/test_attempt_direct_student.py::test_bulk_create_assignments_calls_execute -v
```

Expected: `FAILED` — `AttributeError: 'AttemptRepository' has no attribute ...`

- [ ] **Step 3: Add the two methods to `backend/app/modules/attempt/repository.py`**

Add at the bottom of the `AttemptRepository` class (before the singleton line), after the existing methods. Also add `from sqlalchemy import text` to the existing import line if not already present:

```python
# ── Auto-assignment methods (called by user_service and catalog_service) ──────

async def deactivate_auto_assignments_for_student(
    self, db: AsyncSession, student_id: UUID
) -> None:
    """
    Set is_active=false on all system-created assignments for this student.
    Called when a student changes their grade — clears old grade's exams.
    ONLY touches rows where assigned_by IS NULL (system-assigned).
    Teacher-assigned rows (assigned_by IS NOT NULL) are never touched.
    """
    from sqlalchemy import text
    await db.execute(
        text(
            "UPDATE exam_assignments SET is_active = false "
            "WHERE student_id = :sid AND assigned_by IS NULL"
        ),
        {"sid": student_id},
    )

async def bulk_create_assignments(
    self, db: AsyncSession, rows: list[dict]
) -> None:
    """
    Upsert exam_assignments rows for auto-assignment by grade.
    Each row: {"exam_id": int, "student_id": UUID}

    Uses ON CONFLICT (exam_id, student_id) DO UPDATE SET is_active=true
    WHERE exam_assignments.assigned_by IS NULL
    — meaning: if a manually-assigned row exists for this pair, leave it alone.
    The student already has access; we don't create a duplicate auto row.

    Note: exam_assignments has NO updated_at column — do not add it.
    """
    from sqlalchemy import text
    for row in rows:
        await db.execute(
            text(
                "INSERT INTO exam_assignments "
                "(exam_id, student_id, assignment_type, assigned_by, max_attempts, is_active) "
                "VALUES (:exam_id, :student_id, 'practice', NULL, 10, true) "
                "ON CONFLICT (exam_id, student_id) DO UPDATE "
                "SET is_active = true "
                "WHERE exam_assignments.assigned_by IS NULL"
            ),
            {"exam_id": row["exam_id"], "student_id": row["student_id"]},
        )
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/preetam/Documents/AI/scholarpath && \
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/pytest \
  backend/tests/test_attempt_direct_student.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/attempt/repository.py \
        backend/tests/test_attempt_direct_student.py
git commit -m "feat(attempt): add bulk_create_assignments and deactivate_auto_assignments_for_student to repository"
```

---

## Task 3: Catalog schemas, repository, and service for event management

**Files:**
- Modify: `backend/app/modules/catalog/schemas.py`
- Modify: `backend/app/modules/catalog/repository.py`
- Modify: `backend/app/modules/catalog/service.py`
- Test: `backend/tests/test_catalog_events.py` (new)

**Context:** Admin needs to create a new exam_event ("test") and have Paper I + Paper II created automatically under it. Sections and topics are cloned from the existing seeded event. `publish_exam()` must trigger auto-assignment after it activates an exam.

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_catalog_events.py`:

```python
"""Tests for exam event (test set) creation and auto-assignment on publish."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.catalog.schemas import CreateEventRequest

def test_create_event_request_schema():
    """CreateEventRequest validates required fields."""
    req = CreateEventRequest(
        title_en="MSCE 2024 Practice Set",
        std_class=5,
        year=2024,
        board_id=1,
        category_id=1,
    )
    assert req.year == 2024
    assert req.std_class == 5

def test_create_event_request_rejects_invalid_class():
    """std_class must be 5 or 8."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CreateEventRequest(
            title_en="Bad",
            std_class=6,  # invalid
            year=2024,
            board_id=1,
            category_id=1,
        )
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/preetam/Documents/AI/scholarpath && \
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/pytest \
  backend/tests/test_catalog_events.py -v
```

Expected: `FAILED` — `ImportError: cannot import name 'CreateEventRequest'`

- [ ] **Step 3: Add schemas to `backend/app/modules/catalog/schemas.py`**

Append after the existing `PublishExamResponse` class:

```python
# ── Admin: Create Event (Test Set) ────────────────────────────────────────────

from pydantic import field_validator

class CreateEventRequest(BaseModel):
    """Body for POST /api/admin/catalog/events."""
    title_en: str
    title_mr: Optional[str] = None
    std_class: int
    year: int
    board_id: int
    category_id: int

    @field_validator("std_class")
    @classmethod
    def validate_std_class(cls, v: int) -> int:
        if v not in (5, 8):
            raise ValueError("std_class must be 5 or 8")
        return v


class EventWithExamsResponse(BaseModel):
    """Admin view of an event (test) with its papers' status."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title_en: str
    title_mr: Optional[str]
    std_class: int
    year: int
    exams: list[ExamSummaryResponse] = []
```

- [ ] **Step 4: Add repository methods to `backend/app/modules/catalog/repository.py`**

Append after `set_exam_active`:

```python
async def create_event(
    self,
    db: AsyncSession,
    *,
    board_id: int,
    category_id: int,
    title_en: str,
    title_mr: str | None,
    std_class: int,
    year: int,
) -> ExamEvent:
    """Insert a new exam_event row (draft state, is_active defaults to False)."""
    event = ExamEvent(
        board_id=board_id,
        category_id=category_id,
        title_en=title_en,
        title_mr=title_mr,
        std_class=std_class,
        year=year,
        is_active=False,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event

async def create_exam_under_event(
    self,
    db: AsyncSession,
    *,
    event_id: int,
    paper_code: str,
    set_code: str,
    title_en: str,
    title_mr: str | None = None,
) -> Exam:
    """Insert an exam (paper) under an event. Returns the new Exam row."""
    exam = Exam(
        event_id=event_id,
        paper_code=paper_code,
        set_code=set_code,
        title_en=title_en,
        title_mr=title_mr,
        is_active=False,
    )
    db.add(exam)
    await db.flush()
    await db.refresh(exam)
    return exam

async def clone_sections_and_topics(
    self,
    db: AsyncSession,
    *,
    source_exam_id: int,
    target_exam_id: int,
) -> None:
    """
    Clone sections + topics from source_exam_id into target_exam_id.
    Used when creating a new test to replicate the existing structure.
    Queries sections via selectinload(topics).
    """
    source = await self.get_exam_by_id(db, source_exam_id)
    if source is None:
        return
    for src_section in source.sections:
        new_section = Section(
            exam_id=target_exam_id,
            section_label=src_section.section_label,
            subject_en=src_section.subject_en,
            subject_mr=src_section.subject_mr,
            question_from=src_section.question_from,
            question_to=src_section.question_to,
            order_index=src_section.order_index,
            color_hex=src_section.color_hex,
        )
        db.add(new_section)
        await db.flush()
        await db.refresh(new_section)
        for src_topic in src_section.topics:
            db.add(Topic(
                section_id=new_section.id,
                name_en=src_topic.name_en,
                name_mr=src_topic.name_mr,
                description_en=src_topic.description_en,
                description_mr=src_topic.description_mr,
                order_index=src_topic.order_index,
            ))
    await db.flush()
```

Make sure `Section` and `Topic` are in the import at the top: `from app.modules.catalog.models import Exam, ExamBoard, ExamEvent, Section, Topic`

- [ ] **Step 5: Add service methods to `backend/app/modules/catalog/service.py`**

Append after `unpublish_exam`:

```python
async def create_event_with_papers(
    self,
    db: AsyncSession,
    data: "CreateEventRequest",
) -> "EventWithExamsResponse":
    """
    Create a new exam_event with Paper I (501) and Paper II (502).
    set_code is set to the 4-digit year to avoid UNIQUE(paper_code, set_code) collisions.
    Sections and topics are cloned from the existing Paper I of the same board.
    """
    from app.modules.catalog.schemas import CreateEventRequest, EventWithExamsResponse

    event = await catalog_repository.create_event(
        db,
        board_id=data.board_id,
        category_id=data.category_id,
        title_en=data.title_en,
        title_mr=data.title_mr,
        std_class=data.std_class,
        year=data.year,
    )

    set_code = str(data.year)

    paper1 = await catalog_repository.create_exam_under_event(
        db,
        event_id=event.id,
        paper_code="501",
        set_code=set_code,
        title_en=f"{data.title_en} — Paper I",
        title_mr=f"{data.title_mr} — Paper I" if data.title_mr else None,
    )
    paper2 = await catalog_repository.create_exam_under_event(
        db,
        event_id=event.id,
        paper_code="502",
        set_code=set_code,
        title_en=f"{data.title_en} — Paper II",
        title_mr=f"{data.title_mr} — Paper II" if data.title_mr else None,
    )

    # Clone sections + topics from the seeded exams (exam_id 1 → Paper I template)
    # Find existing Paper I for same board to use as template
    existing = await catalog_repository.list_exams(
        db, board_id=data.board_id, include_inactive=True
    )
    paper1_template = next((e for e in existing if e.paper_code == "501" and e.id != paper1.id), None)
    paper2_template = next((e for e in existing if e.paper_code == "502" and e.id != paper2.id), None)

    if paper1_template:
        await catalog_repository.clone_sections_and_topics(
            db, source_exam_id=paper1_template.id, target_exam_id=paper1.id
        )
    if paper2_template:
        await catalog_repository.clone_sections_and_topics(
            db, source_exam_id=paper2_template.id, target_exam_id=paper2.id
        )

    await db.commit()

    paper1_fresh = await self.get_exam(db, paper1.id)
    paper2_fresh = await self.get_exam(db, paper2.id)

    from app.modules.catalog.schemas import ExamSummaryResponse
    return EventWithExamsResponse(
        id=event.id,
        title_en=event.title_en,
        title_mr=event.title_mr,
        std_class=event.std_class,
        year=event.year,
        exams=[
            ExamSummaryResponse.model_validate(paper1_fresh),
            ExamSummaryResponse.model_validate(paper2_fresh),
        ],
    )

async def auto_assign_exam_to_grade(
    self,
    db: AsyncSession,
    exam_id: int,
    std_class: int,
) -> int:
    """
    Auto-assign an exam to all students whose std_class matches.
    Returns the count of students assigned.
    Called by publish_exam() after activating a paper.
    Calls attempt_repository.bulk_create_assignments (attempt module owns exam_assignments).
    """
    from sqlalchemy import text
    from app.modules.attempt.repository import attempt_repository

    # Fetch all student UUIDs with matching std_class
    result = await db.execute(
        text(
            "SELECT id FROM user_profiles "
            "WHERE std_class = :cls AND role = 'student' AND is_active = true"
        ),
        {"cls": std_class},
    )
    student_ids = [row[0] for row in result.fetchall()]

    if not student_ids:
        return 0

    rows = [{"exam_id": exam_id, "student_id": sid} for sid in student_ids]
    await attempt_repository.bulk_create_assignments(db, rows)
    await db.commit()
    return len(student_ids)
```

Also update `publish_exam` to call `auto_assign_exam_to_grade` and return the count. Replace the existing `publish_exam` method:

```python
async def publish_exam(self, db: AsyncSession, exam_id: int) -> dict:
    """
    Set is_active=True on an exam, making it visible to students.
    Also auto-assigns the exam to all students of the matching grade.
    Admin only — router enforces require_admin.
    Returns: {"exam_id", "is_active", "auto_assigned_count"}
    """
    exam = await self.get_exam(db, exam_id)
    await catalog_repository.set_exam_active(db, exam_id, is_active=True)
    await db.commit()   # always commit is_active=True regardless of auto-assignment

    # Get std_class from exam_event — eager-load event if needed
    event = exam.event
    std_class = event.std_class if event else None
    auto_count = 0
    if std_class in (5, 8):
        auto_count = await self.auto_assign_exam_to_grade(db, exam_id, std_class)

    return {"exam_id": exam_id, "is_active": True, "auto_assigned_count": auto_count}
```

Note: `auto_assign_exam_to_grade` also calls `db.commit()` at its end (for the assignment rows). That is fine — two commits in one request is acceptable when they guard different concerns.

Note: `unpublish_exam` keeps its original return type (`Exam`). Its router callers don't need changes.

- [ ] **Step 6: Run tests**

```bash
cd /Users/preetam/Documents/AI/scholarpath && \
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/pytest \
  backend/tests/test_catalog_events.py -v
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/modules/catalog/schemas.py \
        backend/app/modules/catalog/repository.py \
        backend/app/modules/catalog/service.py \
        backend/tests/test_catalog_events.py
git commit -m "feat(catalog): add event creation, clone sections/topics, auto-assign on publish"
```

---

## Task 4: Catalog admin router — new event endpoints

**Files:**
- Modify: `backend/app/modules/catalog/router.py`

**Context:** Three new admin-only endpoints. The router already has a `router` (public) and registers exam operations. Add event endpoints to the existing admin/catalog pattern.

- [ ] **Step 1: Add admin event endpoints to `backend/app/modules/catalog/router.py`**

First read the current file to see the existing admin_router section, then append:

```python
# ── Admin: Event (Test Set) management ───────────────────────────────────────

from app.modules.catalog.schemas import CreateEventRequest, EventWithExamsResponse

@admin_router.post("/events", response_model=EventWithExamsResponse, status_code=201)
async def create_event(
    data: CreateEventRequest,
    _: UserIdentity = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new exam_event (test set) with Paper I and Paper II auto-created.
    Sections and topics are cloned from the existing papers of the same board.
    """
    return await catalog_service.create_event_with_papers(db, data)


@admin_router.get("/events", response_model=list[EventWithExamsResponse])
async def list_events(
    _: UserIdentity = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all events (including draft) with their papers — for admin UI."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.modules.catalog.models import ExamEvent
    result = await db.execute(
        select(ExamEvent)
        .options(selectinload(ExamEvent.exams))
        .order_by(ExamEvent.year.desc())
    )
    events = list(result.scalars().all())
    from app.modules.catalog.schemas import ExamSummaryResponse
    return [
        EventWithExamsResponse(
            id=e.id,
            title_en=e.title_en,
            title_mr=e.title_mr,
            std_class=e.std_class,
            year=e.year,
            exams=[ExamSummaryResponse.model_validate(ex) for ex in e.exams],
        )
        for e in events
    ]
```

**Important — `catalog/router.py` uses a single-router pattern.** Add an `admin_router` to it:

At the top of `backend/app/modules/catalog/router.py`, after `router = APIRouter()`, add:

```python
admin_router = APIRouter()   # admin-only catalog endpoints
```

Then register it in `backend/app/main.py`. Find the catalog router import and add:

```python
from app.modules.catalog.router import router as catalog_router, admin_router as catalog_admin_router
app.include_router(catalog_admin_router, prefix="/api/admin/catalog", tags=["admin-catalog"])
```

**Also fix the existing publish endpoint in `catalog/router.py` and `admin/router.py`** — `publish_exam` now returns a `dict`, not an `Exam`. Update both callers:

In `backend/app/modules/catalog/router.py` — find the PUT `.../publish` endpoint and change:
```python
# Before:
exam = await catalog_service.publish_exam(db, exam_id)
return PublishExamResponse(id=exam.id, is_active=exam.is_active, ...)

# After:
result = await catalog_service.publish_exam(db, exam_id)
return PublishExamResponse(
    id=result["exam_id"],
    is_active=result["is_active"],
    message=f"Published. Auto-assigned to {result['auto_assigned_count']} students.",
)
```

In `backend/app/modules/admin/router.py` — find the PUT `.../publish` admin endpoint and apply the same dict-access fix.

- [ ] **Step 2: Verify server starts without errors**

```bash
cd /Users/preetam/Documents/AI/scholarpath && \
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app \
  --host 0.0.0.0 --port 8001 --reload &
sleep 3 && curl -s http://localhost:8001/docs | grep -c "openapi" && kill %1
```

Expected: prints `1` (OpenAPI schema loads).

- [ ] **Step 3: Commit**

```bash
git add backend/app/modules/catalog/router.py \
        backend/app/main.py
git commit -m "feat(catalog): add admin_router, register at /api/admin/catalog, add POST /events and GET /events"
```

---

## Task 5: User service — auto-assignment on onboarding and grade change

**Files:**
- Modify: `backend/app/modules/user/service.py`
- Test: `backend/tests/test_user_auto_assign.py` (new)

**Context:** `complete_profile` (onboarding) and `update_my_profile` (grade change) must call auto-assignment when `std_class` is 5 or 8. Grade change additionally deactivates old assignments first.

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_user_auto_assign.py`:

```python
"""Tests for auto-assignment triggered from user service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_complete_profile_triggers_auto_assign_for_class5():
    """complete_profile calls bulk_create_assignments when std_class=5."""
    from app.modules.user.service import UserService
    from app.modules.user.schemas import CompleteProfileRequest

    service = UserService()
    db = AsyncMock()
    user_id = uuid4()

    mock_profile = MagicMock()
    mock_profile.role = "student"
    mock_profile.std_class = 5

    with patch("app.modules.user.repository.user_repository.get_by_id",
               return_value=mock_profile), \
         patch("app.modules.user.repository.user_repository.update",
               return_value=mock_profile), \
         patch("app.modules.user.service.UserService._auto_assign_by_grade",
               new_callable=AsyncMock) as mock_assign:
        req = CompleteProfileRequest(std_class=5, is_onboarded=True)
        await service.complete_profile(db, user_id, req)
        mock_assign.assert_awaited_once_with(db, user_id, 5)


@pytest.mark.asyncio
async def test_complete_profile_skips_auto_assign_when_std_class_none():
    """complete_profile does not call auto-assign when std_class is None."""
    from app.modules.user.service import UserService
    from app.modules.user.schemas import CompleteProfileRequest

    service = UserService()
    db = AsyncMock()
    user_id = uuid4()

    mock_profile = MagicMock()
    mock_profile.role = "parent"
    mock_profile.std_class = None

    with patch("app.modules.user.repository.user_repository.get_by_id",
               return_value=mock_profile), \
         patch("app.modules.user.repository.user_repository.update",
               return_value=mock_profile), \
         patch("app.modules.user.service.UserService._auto_assign_by_grade",
               new_callable=AsyncMock) as mock_assign:
        req = CompleteProfileRequest(is_onboarded=True)
        await service.complete_profile(db, user_id, req)
        mock_assign.assert_not_awaited()
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd /Users/preetam/Documents/AI/scholarpath && \
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/pytest \
  backend/tests/test_user_auto_assign.py -v
```

Expected: `FAILED` — `_auto_assign_by_grade` not found.

- [ ] **Step 3: Update `backend/app/modules/user/service.py`**

Add the helper method and update `complete_profile` and `update_my_profile`:

```python
# Add this helper anywhere in UserService class:

async def _auto_assign_by_grade(
    self,
    db: AsyncSession,
    student_id: uuid.UUID,
    std_class: int,
) -> None:
    """
    Auto-assign all active exams for this grade to the student.
    Guard: only fires if std_class is 5 or 8.
    Grade change: deactivate old auto-assignments first.
    """
    if std_class not in (5, 8):
        return
    from app.modules.attempt.repository import attempt_repository
    from app.modules.catalog.repository import catalog_repository

    # Deactivate old grade's auto-assignments before assigning new grade
    await attempt_repository.deactivate_auto_assignments_for_student(db, student_id)

    # Fetch all active exams for the new grade
    from sqlalchemy import text
    result = await db.execute(
        text(
            "SELECT e.id FROM exams e "
            "JOIN exam_events ev ON e.event_id = ev.id "
            "WHERE e.is_active = true AND ev.std_class = :cls"
        ),
        {"cls": std_class},
    )
    exam_ids = [row[0] for row in result.fetchall()]

    if not exam_ids:
        return

    rows = [{"exam_id": eid, "student_id": student_id} for eid in exam_ids]
    await attempt_repository.bulk_create_assignments(db, rows)
```

Update `complete_profile` — after the `updated = await user_repository.update(db, user_id, updates)` line, add:

```python
    # Auto-assign exams for the student's grade
    new_std_class = updates.get("std_class") or (updated.std_class if updated else None)
    if new_std_class in (5, 8):
        await self._auto_assign_by_grade(db, user_id, new_std_class)
```

Update `update_my_profile` — after `profile = await user_repository.update(...)`, add:

```python
    # Trigger auto-assignment if std_class was included and is valid
    new_std_class = updates.get("std_class")
    if new_std_class in (5, 8):
        await self._auto_assign_by_grade(db, user_id, new_std_class)
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/preetam/Documents/AI/scholarpath && \
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/pytest \
  backend/tests/test_user_auto_assign.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/user/service.py \
        backend/tests/test_user_auto_assign.py
git commit -m "feat(user): auto-assign exams by grade on onboarding and grade change"
```

---

## Task 6: Dashboard backend — ExamWithAssignmentResponse

**Files:**
- Modify: `backend/app/modules/admin/schemas.py`
- Modify: `backend/app/modules/admin/router.py:39-119`

**Context:** The student dashboard must return assignment metadata (attempts_used, max_attempts, assignment_id, event_title, etc.) so the frontend can group by test and show attempt counts.

- [ ] **Step 1: Add `ExamWithAssignmentResponse` to `backend/app/modules/admin/schemas.py`**

After the `StudentDashboardResponse` class, add:

```python
class ExamWithAssignmentResponse(BaseModel):
    """
    Exam card enriched with assignment metadata for the student dashboard.
    Extends ExamSummaryResponse fields with event grouping + attempt tracking.
    """
    # From exam
    id: int
    event_id: int
    paper_code: str
    set_code: str
    title_en: str
    title_mr: Optional[str]
    medium: str
    total_questions: int
    total_marks: int
    duration_minutes: int
    is_active: bool
    is_accessible: Optional[bool] = True

    # From exam_event (for frontend grouping)
    event_title: str
    event_year: int
    std_class: int

    # From exam_assignments
    assignment_id: Optional[int] = None
    attempts_used: int = 0
    max_attempts: int = 10
    valid_until: Optional[datetime] = None
    assignment_type: str = "practice"
    assigned_by_name: Optional[str] = None
```

Also update `StudentDashboardResponse` to use the new type:

```python
class StudentDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    available_exams: List[ExamWithAssignmentResponse]   # was List[ExamSummaryResponse]
    recent_attempts: List[AttemptSummary]
    stats: StudentDashboardStats
```

- [ ] **Step 2: Rewrite `get_student_dashboard` in `backend/app/modules/admin/router.py`**

Replace the entire `get_student_dashboard` function (lines 39-119) with:

```python
@router.get("/dashboard/student", response_model=StudentDashboardResponse)
async def get_student_dashboard(
    child_id: UUID | None = None,
    current_user: UserIdentity = Depends(require_role("student", "parent")),
    db: AsyncSession = Depends(get_db)
):
    """
    Student dashboard: returns assigned exams with attempt metadata,
    recent attempts, and summary stats.
    """
    from app.modules.user.repository import user_repository
    from app.shared.exceptions import Forbidden
    from sqlalchemy import text

    target_id = current_user.id
    if current_user.role == "parent":
        if not child_id:
            target_id = None
        else:
            from app.modules.user.child_repository import ChildRepository
            child_repo = ChildRepository()
            child = await child_repo.get_by_id(child_id, current_user.id, db)
            if not child:
                raise Forbidden("Not authorized to view this child's dashboard")
            target_id = child_id

    # Fetch assigned exams with event and assignment metadata
    available_exams = []
    if target_id is not None:
        rows = await db.execute(
            text("""
                SELECT
                    e.id, e.event_id, e.paper_code, e.set_code,
                    e.title_en, e.title_mr, e.medium,
                    e.total_questions, e.total_marks, e.duration_minutes, e.is_active,
                    ev.title_en  AS event_title,
                    ev.title_mr  AS event_title_mr,
                    ev.year      AS event_year,
                    ev.std_class AS std_class,
                    ea.id        AS assignment_id,
                    ea.attempts_used,
                    ea.max_attempts,
                    ea.valid_until,
                    ea.assignment_type,
                    NULL::text   AS assigned_by_name
                FROM exam_assignments ea
                JOIN exams e ON e.id = ea.exam_id
                JOIN exam_events ev ON ev.id = e.event_id
                WHERE ea.student_id = :sid
                  AND ea.is_active = true
                  AND e.is_active = true
                ORDER BY ev.year DESC, e.paper_code
            """),
            {"sid": target_id},
        )
        for row in rows.mappings():
            available_exams.append(ExamWithAssignmentResponse(
                id=row["id"],
                event_id=row["event_id"],
                paper_code=row["paper_code"],
                set_code=row["set_code"],
                title_en=row["title_en"],
                title_mr=row["title_mr"],
                medium=str(row["medium"]),
                total_questions=row["total_questions"],
                total_marks=row["total_marks"],
                duration_minutes=row["duration_minutes"],
                is_active=row["is_active"],
                event_title=row["event_title"],
                event_year=row["event_year"],
                std_class=row["std_class"],
                assignment_id=row["assignment_id"],
                attempts_used=row["attempts_used"] or 0,
                max_attempts=row["max_attempts"] or 10,
                valid_until=row["valid_until"],
                assignment_type=str(row["assignment_type"]),
                assigned_by_name=row["assigned_by_name"],
            ))

    attempts_orm = []
    if target_id is not None:
        attempts_orm = await attempt_repository.get_all_student_attempts(db, target_id)

    def _status(a) -> str:
        return str(a.status.value if hasattr(a.status, "value") else a.status)

    submitted_attempts = [
        a for a in attempts_orm
        if _status(a) == "submitted" and a.percentage is not None
    ]

    stats = StudentDashboardStats(
        total_attempts=len(attempts_orm),
        avg_percentage=round(
            sum(float(a.percentage) for a in submitted_attempts) / len(submitted_attempts), 1
        ) if submitted_attempts else 0.0,
        best_score=max((a.total_score for a in submitted_attempts if a.total_score), default=0),
        exams_completed=len(set(a.exam_id for a in submitted_attempts)),
    )

    recent = [
        AttemptSummary(
            attempt_id=a.id,
            exam_id=a.exam_id,
            attempt_number=a.attempt_number,
            status=_status(a),
            total_score=a.total_score,
            total_correct=a.total_correct,
            total_wrong=a.total_wrong,
            total_skipped=a.total_skipped,
            percentage=float(a.percentage) if a.percentage is not None else None,
            grade=a.grade,
            started_at=a.started_at,
            submitted_at=a.submitted_at,
        )
        for a in attempts_orm[:5]
    ]

    return StudentDashboardResponse(
        available_exams=available_exams,
        recent_attempts=recent,
        stats=stats,
    )
```

Also add the import at the top of the router file:
```python
from app.modules.admin.schemas import (
    ...
    ExamWithAssignmentResponse,   # add this
)
```

- [ ] **Step 3: Verify no import errors**

```bash
cd /Users/preetam/Documents/AI/scholarpath && \
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python \
  -c "from app.modules.admin.router import router; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/modules/admin/schemas.py \
        backend/app/modules/admin/router.py
git commit -m "feat(dashboard): return ExamWithAssignmentResponse with event grouping and attempt metadata"
```

---

## Task 7: Dashboard frontend — TestGroupCard + PaperRow

**Files:**
- Create: `frontend/src/modules/dashboard/components/TestGroupCard.jsx`
- Create: `frontend/src/modules/dashboard/components/PaperRow.jsx`
- Modify: `frontend/src/modules/dashboard/pages/StudentDashboardPage.jsx`

**Context:** Replace the flat `AvailableExamCard` list with grouped test cards. Each test (event) is collapsible. The first test is expanded by default. PaperRow handles all button states and passes `assignment_id` to the start URL.

- [ ] **Step 1: Create `frontend/src/modules/dashboard/components/PaperRow.jsx`**

```jsx
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

/**
 * PaperRow — a single paper (Paper I or Paper II) inside a TestGroupCard.
 * Handles all button states: Start, Resume, Completed, Locked, Assigned.
 */
export function PaperRow({ exam, ongoingAttemptId }) {
    const { t } = useTranslation()
    const navigate = useNavigate()

    const attemptsLeft = (exam.max_attempts || 10) - (exam.attempts_used || 0)
    const isExhausted = attemptsLeft <= 0
    const isLocked = exam.is_accessible === false
    const hasOngoing = !!ongoingAttemptId
    const isTeacherAssigned = exam.assignment_type === 'assigned' || exam.assignment_type === 'mock_test'

    const startUrl = exam.assignment_id
        ? `/exam/${exam.id}/start?assignment_id=${exam.assignment_id}`
        : `/exam/${exam.id}/start`
    const resumeUrl = ongoingAttemptId ? `/exam/${ongoingAttemptId}/state` : startUrl

    const paperLabel = exam.paper_code === '501' ? 'Paper I' : 'Paper II'
    const title = exam.title_en

    return (
        <div className="flex items-center justify-between px-5 py-3 gap-4">
            {/* Paper info */}
            <div className="flex items-center gap-3 min-w-0">
                <span className="text-surface-400 text-sm font-mono w-16 shrink-0">{paperLabel}</span>
                <div className="min-w-0">
                    <p className="text-sm font-medium text-surface-700 truncate">{title}</p>
                    <div className="flex items-center gap-3 mt-0.5">
                        <span className="text-xs text-surface-400">
                            {exam.total_questions} {t('dashboard.questions', 'Qs')} · {exam.duration_minutes} {t('dashboard.mins', 'min')}
                        </span>
                        {!isExhausted && !isLocked && (
                            <span className="text-xs text-surface-400">
                                {attemptsLeft}/{exam.max_attempts} {t('dashboard.attemptsLeft', 'attempts left')}
                            </span>
                        )}
                        {isTeacherAssigned && (
                            <span className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded font-medium">
                                {t('dashboard.assignedByTeacher', 'Assigned')}
                            </span>
                        )}
                        {exam.valid_until && (
                            <span className="text-xs text-orange-500">
                                {t('dashboard.due', 'Due')} {new Date(exam.valid_until).toLocaleDateString()}
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Action button */}
            {isLocked ? (
                <button
                    onClick={() => navigate('/upgrade')}
                    className="shrink-0 text-sm px-4 py-1.5 bg-amber-500 text-white font-medium rounded-lg hover:bg-amber-600 transition flex items-center gap-1.5"
                >
                    🔒 {t('dashboard.upgrade', 'Upgrade')}
                </button>
            ) : isExhausted ? (
                <span className="shrink-0 text-xs px-3 py-1.5 bg-surface-100 text-surface-400 rounded-lg font-medium">
                    {t('dashboard.completed', 'Completed')} ({exam.max_attempts}/{exam.max_attempts})
                </span>
            ) : hasOngoing ? (
                <Link
                    to={resumeUrl}
                    className="shrink-0 text-sm px-4 py-1.5 bg-orange-500 text-white font-medium rounded-lg hover:bg-orange-600 transition"
                >
                    {t('dashboard.resume', 'Resume →')}
                </Link>
            ) : (
                <Link
                    to={startUrl}
                    className="shrink-0 text-sm px-4 py-1.5 bg-brand-600 text-white font-medium rounded-lg hover:bg-brand-700 transition"
                >
                    {t('dashboard.start', 'Start →')}
                </Link>
            )}
        </div>
    )
}
```

- [ ] **Step 2: Create `frontend/src/modules/dashboard/components/TestGroupCard.jsx`**

```jsx
import { useState } from 'react'
import { PaperRow } from './PaperRow'

/**
 * TestGroupCard — collapsible card grouping Paper I + Paper II for one test (exam_event).
 * defaultOpen: the first card in the list should be open by default.
 */
export function TestGroupCard({ eventTitle, eventYear, stdClass, exams, defaultOpen = false }) {
    const [open, setOpen] = useState(defaultOpen)

    const papersReady = exams.filter(e => e.is_active).length
    const totalPapers = exams.length

    return (
        <div className={`bg-white rounded-xl border shadow-sm overflow-hidden transition ${open ? 'border-brand-200' : 'border-surface-100'}`}>
            {/* Header */}
            <button
                onClick={() => setOpen(o => !o)}
                className="w-full flex items-center justify-between px-5 py-4 hover:bg-surface-50 transition text-left"
            >
                <div>
                    <h3 className="font-bold text-surface-800 text-base">{eventTitle}</h3>
                    <p className="text-xs text-surface-400 mt-0.5">
                        Class {stdClass} · {totalPapers} papers · {papersReady}/{totalPapers} available
                    </p>
                </div>
                <span className={`text-surface-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}>▾</span>
            </button>

            {/* Papers */}
            {open && (
                <div className="border-t border-surface-100 divide-y divide-surface-50">
                    {exams.map(exam => (
                        <PaperRow key={exam.id} exam={exam} ongoingAttemptId={null} />
                    ))}
                    {exams.length === 0 && (
                        <p className="px-5 py-3 text-sm text-surface-400">No papers available yet.</p>
                    )}
                </div>
            )}
        </div>
    )
}
```

- [ ] **Step 3: Update `frontend/src/modules/dashboard/pages/StudentDashboardPage.jsx`**

Replace the `{(!available_exams || available_exams.length === 0) ? ... : ...}` block in the "Available Exams" section with:

```jsx
import { TestGroupCard } from '../components/TestGroupCard'

// Inside the component, group by event before rendering:
const testGroups = available_exams
    ? available_exams.reduce((acc, exam) => {
        const key = exam.event_title || 'Unknown'
        if (!acc[key]) acc[key] = { eventTitle: key, eventYear: exam.event_year, stdClass: exam.std_class, exams: [] }
        acc[key].exams.push(exam)
        return acc
    }, {})
    : {}
const testGroupList = Object.values(testGroups).sort((a, b) => (b.eventYear || 0) - (a.eventYear || 0))

// Replace the section JSX:
<section>
    <h2 className="text-xl font-bold text-surface-800 mb-4">
        {t('dashboard.yourTests', 'Your Tests')}
    </h2>
    {testGroupList.length === 0 ? (
        <div className="bg-surface-50 p-6 rounded-xl border border-surface-200 text-center text-surface-500">
            {t('dashboard.noExams', 'No exams assigned yet.')}
        </div>
    ) : (
        <div className="space-y-4">
            {testGroupList.map((group, idx) => (
                <TestGroupCard
                    key={group.eventTitle}
                    eventTitle={group.eventTitle}
                    eventYear={group.eventYear}
                    stdClass={group.stdClass}
                    exams={group.exams}
                    defaultOpen={idx === 0}
                />
            ))}
        </div>
    )}
</section>
```

Also remove the import of `AvailableExamCard` if it's no longer used.

- [ ] **Step 4: Verify frontend builds**

```bash
cd /Users/preetam/Documents/AI/scholarpath/frontend && npm run build 2>&1 | tail -20
```

Expected: `✓ built in` — no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/modules/dashboard/components/TestGroupCard.jsx \
        frontend/src/modules/dashboard/components/PaperRow.jsx \
        frontend/src/modules/dashboard/pages/StudentDashboardPage.jsx
git commit -m "feat(dashboard): group exams by test (exam_event) with TestGroupCard + PaperRow"
```

---

## Task 8: Admin frontend — CreateTestPage

**Files:**
- Create: `frontend/src/modules/admin/pages/CreateTestPage.jsx`
- Modify: `frontend/src/modules/admin/api/adminApi.js`
- Modify: `frontend/src/modules/admin/store/adminStore.js`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/modules/admin/index.js`

- [ ] **Step 1: Add API methods to `frontend/src/modules/admin/api/adminApi.js`**

Append:

```js
// ── Exam Events (Test Sets) ───────────────────────────────────────────────────
listAllEvents: () =>
    apiClient.get('/api/admin/catalog/events').then(r => r.data),

createTest: (data) =>
    apiClient.post('/api/admin/catalog/events', data).then(r => r.data),
```

- [ ] **Step 2: Add `createTest` to `frontend/src/modules/admin/store/adminStore.js`**

Append after `unpublishExam`:

```js
// ── Create Test ───────────────────────────────────────────────────────────────
createTestLoading: false,
createTestError: null,
createTestSuccess: null,

createTest: async (data) => {
    set({ createTestLoading: true, createTestError: null, createTestSuccess: null })
    try {
        const result = await adminApi.createTest(data)
        set({ createTestLoading: false, createTestSuccess: result })
        // Refresh exams list so new papers appear in Question Manager
        get().fetchAllExams()
        return result
    } catch (e) {
        const msg = e.response?.data?.detail || 'Failed to create test'
        set({ createTestError: msg, createTestLoading: false })
        throw e
    }
},
```

Also update `publishExam` to capture and store `auto_assigned_count` from the response:

```js
publishExam: async (examId) => {
    try {
        const result = await adminApi.publishExam(examId)
        set(state => ({
            exams: state.exams.map(ex => ex.id === examId ? { ...ex, is_active: true } : ex),
            lastPublishResult: result,   // { exam_id, is_active, auto_assigned_count }
        }))
    } catch (e) {
        throw e
    }
},
```

Add `lastPublishResult: null` to the initial state.

- [ ] **Step 3: Create `frontend/src/modules/admin/pages/CreateTestPage.jsx`**

```jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAdminStore } from '../store/adminStore'

const BOARD_ID = 1       // MSCE Maharashtra (seeded)
const CATEGORY_ID = 1    // Pre-Upper Primary Scholarship (seeded)

export function CreateTestPage() {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const { createTest, createTestLoading, createTestError } = useAdminStore()

    const [form, setForm] = useState({
        title_en: '',
        title_mr: '',
        std_class: '5',
        year: new Date().getFullYear(),
    })
    const [success, setSuccess] = useState(null)

    const handleSubmit = async (e) => {
        e.preventDefault()
        try {
            const result = await createTest({
                title_en: form.title_en,
                title_mr: form.title_mr || null,
                std_class: parseInt(form.std_class),
                year: parseInt(form.year),
                board_id: BOARD_ID,
                category_id: CATEGORY_ID,
            })
            setSuccess(result)
        } catch (_) { /* error shown via store */ }
    }

    if (success) {
        return (
            <div className="p-8 max-w-xl mx-auto">
                <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
                    <div className="text-3xl mb-3">✅</div>
                    <h2 className="text-xl font-bold text-green-800 mb-2">Test Created!</h2>
                    <p className="text-green-700 mb-1"><strong>{success.title_en}</strong></p>
                    <p className="text-sm text-green-600 mb-4">
                        {success.exams?.length || 2} papers created (Draft).
                        Go to Question Manager to import questions.
                    </p>
                    <div className="flex gap-3 justify-center">
                        <button
                            onClick={() => navigate('/admin/questions')}
                            className="px-5 py-2 bg-brand-600 text-white rounded-xl font-semibold hover:bg-brand-700"
                        >
                            Import Questions →
                        </button>
                        <button
                            onClick={() => { setSuccess(null); setForm({ title_en: '', title_mr: '', std_class: '5', year: new Date().getFullYear() }) }}
                            className="px-5 py-2 bg-surface-100 text-surface-700 rounded-xl font-semibold hover:bg-surface-200"
                        >
                            Create Another
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="p-4 sm:p-8 max-w-xl mx-auto">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-surface-900">Create New Test</h1>
                <p className="text-surface-500 mt-1">
                    Creates Paper I and Paper II automatically. Import questions separately.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-surface-100 shadow-sm p-6 space-y-5">
                <div>
                    <label className="block text-sm font-semibold text-surface-700 mb-1.5">
                        Title (English) <span className="text-red-500">*</span>
                    </label>
                    <input
                        type="text"
                        required
                        placeholder="e.g. MSCE 2024 Practice Set"
                        value={form.title_en}
                        onChange={e => setForm(f => ({ ...f, title_en: e.target.value }))}
                        className="w-full px-4 py-2.5 border border-surface-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
                    />
                </div>

                <div>
                    <label className="block text-sm font-semibold text-surface-700 mb-1.5">
                        Title (Marathi) <span className="text-surface-400 font-normal">(optional)</span>
                    </label>
                    <input
                        type="text"
                        placeholder="मराठी शीर्षक"
                        value={form.title_mr}
                        onChange={e => setForm(f => ({ ...f, title_mr: e.target.value }))}
                        className="w-full px-4 py-2.5 border border-surface-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-semibold text-surface-700 mb-1.5">Grade</label>
                        <select
                            value={form.std_class}
                            onChange={e => setForm(f => ({ ...f, std_class: e.target.value }))}
                            className="w-full px-4 py-2.5 border border-surface-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-300 bg-white"
                        >
                            <option value="5">Class 5</option>
                            <option value="8">Class 8</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-semibold text-surface-700 mb-1.5">Year</label>
                        <input
                            type="number"
                            required
                            min="2020"
                            max="2035"
                            value={form.year}
                            onChange={e => setForm(f => ({ ...f, year: e.target.value }))}
                            className="w-full px-4 py-2.5 border border-surface-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-300"
                        />
                    </div>
                </div>

                <div className="bg-surface-50 rounded-lg p-4 text-sm text-surface-600">
                    <p className="font-medium text-surface-700 mb-1">What gets created:</p>
                    <ul className="space-y-0.5 text-surface-500 list-disc list-inside">
                        <li>Paper I — English + Mathematics (75 questions)</li>
                        <li>Paper II — Marathi + Intelligence Test (75 questions)</li>
                        <li>All sections and topics (cloned from existing structure)</li>
                    </ul>
                </div>

                {createTestError && (
                    <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">{createTestError}</p>
                )}

                <button
                    type="submit"
                    disabled={createTestLoading || !form.title_en}
                    className="w-full py-3 bg-brand-600 text-white font-bold rounded-xl hover:bg-brand-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {createTestLoading ? 'Creating…' : 'Create Test →'}
                </button>
            </form>
        </div>
    )
}
```

- [ ] **Step 4: Add route to `frontend/src/App.jsx`**

Find the admin routes section and add:

```jsx
import { CreateTestPage } from '@/modules/admin'
// ...
<Route path="/admin/tests/new" element={<CreateTestPage />} />
```

- [ ] **Step 5: Export from `frontend/src/modules/admin/index.js`**

Add `CreateTestPage` to the existing exports:

```js
export { CreateTestPage } from './pages/CreateTestPage'
```

- [ ] **Step 6: Verify frontend builds**

```bash
cd /Users/preetam/Documents/AI/scholarpath/frontend && npm run build 2>&1 | tail -20
```

Expected: `✓ built in` — no errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/modules/admin/pages/CreateTestPage.jsx \
        frontend/src/modules/admin/api/adminApi.js \
        frontend/src/modules/admin/store/adminStore.js \
        frontend/src/modules/admin/index.js \
        frontend/src/App.jsx
git commit -m "feat(admin): add CreateTestPage with auto paper creation at /admin/tests/new"
```

---

## Task 9: Admin frontend — ExamPublisherPage updates

**Files:**
- Modify: `frontend/src/modules/admin/pages/ExamPublisherPage.jsx`

**Context:** Show grade label per test group and show `auto_assigned_count` toast after publish.

- [ ] **Step 1: Update `frontend/src/modules/admin/pages/ExamPublisherPage.jsx`**

1. Read `lastPublishResult` from the store in the component:
```jsx
const { ..., lastPublishResult } = useAdminStore()
```

2. Show auto-assign count in the success message. Replace the existing `setActionSuccess(...)` call in `handleToggle`:
```jsx
if (exam.is_active) {
    await unpublishExam(exam.id)
    setActionSuccess(`"${exam.title_en}" has been unpublished.`)
} else {
    await publishExam(exam.id)
    const count = useAdminStore.getState().lastPublishResult?.auto_assigned_count ?? 0
    setActionSuccess(`"${exam.title_en}" is now live. Auto-assigned to ${count} students.`)
}
```

3. Add grade label to event header. In the event header div, after the title:
```jsx
{eventExams[0]?.std_class && (
    <span className="text-xs bg-brand-100 text-brand-700 px-2 py-0.5 rounded-full font-medium ml-2">
        Class {eventExams[0].std_class}
    </span>
)}
```

**Add `std_class` to `AdminExamRow`.**

In `backend/app/modules/admin/schemas.py`, add to `AdminExamRow`:
```python
std_class: Optional[int] = None
```

In `backend/app/modules/admin/router.py`, find the `GET /api/admin/catalog/exams` endpoint. It runs a raw SQL query that builds `AdminExamRow` objects. Add `ev.std_class` to that SELECT and map it in the row construction:
```python
# In the SELECT, add:
ev.std_class,
# In the AdminExamRow(...) construction, add:
std_class=row["std_class"],
```

Then in `ExamPublisherPage.jsx`, read `exam.std_class` from the exam row (which now carries the field).

- [ ] **Step 2: Also add "Create Test" nav link to Admin sidebar or dashboard**

In `frontend/src/modules/admin/pages/AdminDashboardPage.jsx`, add a quick-action card or link to `/admin/tests/new`.

- [ ] **Step 3: Verify frontend builds**

```bash
cd /Users/preetam/Documents/AI/scholarpath/frontend && npm run build 2>&1 | tail -20
```

Expected: `✓ built in` — no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/modules/admin/pages/ExamPublisherPage.jsx \
        frontend/src/modules/admin/pages/AdminDashboardPage.jsx \
        backend/app/modules/admin/schemas.py \
        backend/app/modules/admin/router.py
git commit -m "feat(admin): show grade label and auto-assign count on ExamPublisherPage"
```

---

## Task 10: Data fix — update existing seeded exam set_codes

**Context:** The seeded exams have `set_code='A'`. New tests use `set_code=year` (e.g. `'2025'`). This SQL must be run once in the Supabase SQL Editor to make the seeded data consistent with the new convention.

- [ ] **Step 1: Run this SQL in Supabase SQL Editor**

```sql
-- Update existing seeded exams: set_code 'A' → '2025'
-- (The seeded event is MSCE 5th Std 2025, so year=2025 is correct)
UPDATE exams
SET set_code = '2025'
WHERE set_code = 'A'
  AND paper_code IN ('501', '502');

-- Verify
SELECT id, paper_code, set_code, title_en FROM exams ORDER BY id;
```

Expected: 2 rows with `set_code='2025'`.

- [ ] **Step 2: Commit a note**

```bash
git commit --allow-empty -m "chore: applied set_code data fix (A→2025) in Supabase SQL Editor"
```

---

## Verification Checklist

After all tasks:

- [ ] `POST /api/attempts/start` works without `child_profile_id` (direct student)
- [ ] `attempts_used` increments after a direct-student submission
- [ ] New student completing onboarding gets auto-assigned active exams
- [ ] Student changing grade gets old assignments deactivated and new ones created
- [ ] Admin can create a new test at `/admin/tests/new`
- [ ] New test appears in Question Manager exam selector
- [ ] Publishing a paper returns `auto_assigned_count` and assigns to matching students
- [ ] Student dashboard groups exams by test with collapsible cards
- [ ] First test group is expanded by default
- [ ] ExamPublisherPage shows grade label per event
