# WS2: Parent & Child Module Gaps — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 3 backend issues in the parent/child layer: architecture clarity (singleton pattern + Pydantic v2), SQL-level pagination, and a SQL injection guard.

**Architecture:** All changes are in `backend/app/modules/user/` and `backend/app/modules/analysis/`. No frontend changes. TDD using existing pytest setup. One commit per fix.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, pytest with asyncio_mode=auto.

**Spec:** `docs/superpowers/specs/2026-04-07-production-readiness-cleanup-design.md` — fixes P1–P3.

**Prerequisite:** WS1 branch merged to main. Check out from updated main:
```bash
git checkout main && git pull && git checkout -b fix/parent-child-module
```

**Test command:**
```bash
DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/modules/user/tests/ -v --tb=short
```

---

## Task 1: P1 — Parent service architecture clarity

**Problem:** `child_repository` is instantiated inside `ParentService.__init__()` (not a singleton). All `self.child_repo` call sites will break after the fix if not all updated. `child_schemas.py` uses Pydantic v1 `class Config` style. No docstring explaining the ADR-009 vs ADR-013 split.

**Files:**
- Modify: `backend/app/modules/user/child_repository.py` (add module-level singleton)
- Modify: `backend/app/modules/user/parent_service.py` (remove init, replace all `self.child_repo`, add docstring)
- Modify: `backend/app/modules/user/child_schemas.py` (Pydantic v2 style)
- Create: `backend/app/modules/user/tests/test_child_repository.py` (singleton test)
- Modify: `backend/app/modules/user/tests/test_parent_service.py` (init + schema tests)

- [ ] **Step 1: Read all affected files before touching anything**

  Read these files in full:
  - `backend/app/modules/user/child_repository.py`
  - `backend/app/modules/user/parent_service.py`
  - `backend/app/modules/user/child_schemas.py`

  Count exactly how many times `self.child_repo` appears in `parent_service.py` (there should be ~6 call sites). Note each line number.

- [ ] **Step 2: Write the failing tests (in two files)**

  Create `backend/app/modules/user/tests/test_child_repository.py`:

  ```python
  """Tests for child_repository singleton pattern."""


  def test_child_repository_is_module_level_singleton():
      """child_repository.py must export a module-level singleton instance."""
      from app.modules.user import child_repository as cr_module
      assert hasattr(cr_module, 'child_repository'), (
          "child_repository.py must define: child_repository = ChildRepository() "
          "at module level (singleton pattern per CLAUDE.md)"
      )
      from app.modules.user.child_repository import child_repository
      assert isinstance(child_repository, cr_module.ChildRepository)
  ```

  Append to `backend/app/modules/user/tests/test_parent_service.py`:

  ```python
  def test_parent_service_does_not_instantiate_child_repo_in_init():
      """ParentService.__init__ must not create ChildRepository() — import the singleton."""
      import inspect
      from app.modules.user.parent_service import ParentService
      init_source = inspect.getsource(ParentService.__init__)
      assert 'ChildRepository()' not in init_source, (
          "ParentService.__init__ must not instantiate ChildRepository(). "
          "Import the module-level singleton instead."
      )


  def test_child_schema_uses_pydantic_v2_model_config():
      """child_schemas.py must use Pydantic v2 model_config, not v1 class Config."""
      from app.modules.user.child_schemas import ChildProfileSchema
      assert hasattr(ChildProfileSchema, 'model_config'), (
          "ChildProfileSchema must use model_config = ConfigDict(...) not class Config"
      )
  ```

- [ ] **Step 3: Run tests to verify they fail**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest \
    backend/app/modules/user/tests/test_child_repository.py::test_child_repository_is_module_level_singleton \
    backend/app/modules/user/tests/test_parent_service.py::test_parent_service_does_not_instantiate_child_repo_in_init \
    backend/app/modules/user/tests/test_parent_service.py::test_child_schema_uses_pydantic_v2_model_config \
    -v
  ```
  Expected: All 3 `FAILED`.

- [ ] **Step 4: Add singleton to child_repository.py**

  At the very end of `backend/app/modules/user/child_repository.py`, after the class definition, add:

  ```python
  # Module-level singleton — import this, never instantiate ChildRepository() directly
  child_repository = ChildRepository()
  ```

- [ ] **Step 5: Fix parent_service.py — singleton import and call sites**

  In `backend/app/modules/user/parent_service.py`:

  1. Change the import at line 13 from:
     ```python
     from app.modules.user.child_repository import ChildRepository
     ```
     to:
     ```python
     from app.modules.user.child_repository import child_repository
     ```

  2. In `ParentService.__init__()`, remove the line:
     ```python
     self.child_repo = ChildRepository()
     ```

  3. Replace **every** occurrence of `self.child_repo` in the file with `child_repository`. Do not miss any — search for all occurrences with:
     ```bash
     grep -n "self\.child_repo" backend/app/modules/user/parent_service.py
     ```
     There should be zero remaining after the replacement.

- [ ] **Step 6: Add module docstring to parent_service.py**

  At the very top of `backend/app/modules/user/parent_service.py`, after any existing imports, add:

  ```python
  """
  Parent service — business logic for parent monitoring features.

  Two data models are used here — understand the distinction before editing:

  ADR-009 (parent_student_links):
    A parent linked to an *existing student account* via email.
    All methods using `parent_repository` operate on this model.
    Example: link_child(), get_dashboard(), get_child_detail() when student_id is provided.

  ADR-013 (child_profiles):
    A profile created BY the parent for a child who has NO Supabase account yet.
    All methods using `child_repository` operate on this model.
    Example: get_child_attempts(), get_attempt_wrong_answers() when child_profile_id is provided.

  A method must never mix both models without an explicit comment explaining why.
  """
  ```

- [ ] **Step 7: Fix child_schemas.py — Pydantic v2 style**

  In `backend/app/modules/user/child_schemas.py`:

  1. Add import at the top if not present:
     ```python
     from pydantic import ConfigDict
     ```

  2. Replace the `class Config:` block inside `ChildProfileSchema`:
     ```python
     # Remove this:
     class Config:
         from_attributes = True

     # Replace with this (at class level, before any fields):
     model_config = ConfigDict(from_attributes=True)
     ```

- [ ] **Step 8: Run tests to verify they pass**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest \
    backend/app/modules/user/tests/test_child_repository.py::test_child_repository_is_module_level_singleton \
    backend/app/modules/user/tests/test_parent_service.py::test_parent_service_does_not_instantiate_child_repo_in_init \
    backend/app/modules/user/tests/test_parent_service.py::test_child_schema_uses_pydantic_v2_model_config \
    -v
  ```
  Expected: `3 passed`

- [ ] **Step 9: Run full user module test suite to catch regressions**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/modules/user/tests/ -v --tb=short
  ```
  Expected: All tests pass.

- [ ] **Step 10: Commit**

  ```bash
  git add backend/app/modules/user/child_repository.py \
          backend/app/modules/user/parent_service.py \
          backend/app/modules/user/child_schemas.py \
          backend/app/modules/user/tests/test_child_repository.py \
          backend/app/modules/user/tests/test_parent_service.py
  git commit -m "fix: child_repository singleton, replace self.child_repo callsites, Pydantic v2 child_schemas"
  ```

---

## Task 2: P2 — SQL-level pagination for child attempts

**Problem:** `parent_service.get_child_attempts_paged()` calls `parent_repository.get_child_attempts(limit=200)` then slices in Python. Loads far too many rows per request. The repo already has `limit` and `LIMIT :lim` — only `offset` and a COUNT method need adding.

**Files:**
- Modify: `backend/app/modules/user/parent_repository.py`
- Modify: `backend/app/modules/user/parent_service.py`
- Test: `backend/app/modules/user/tests/test_parent_service.py`

- [ ] **Step 1: Read the current pagination code**

  Read:
  - `parent_repository.get_child_attempts()` — note the current SQL (has `LIMIT :lim`)
  - `parent_service.get_child_attempts_paged()` — note the Python slice logic

- [ ] **Step 2: Write the failing tests**

  In `backend/app/modules/user/tests/test_parent_service.py`, add:

  ```python
  @pytest.mark.asyncio
  async def test_get_child_attempts_paged_uses_sql_offset_not_python_slice():
      """
      get_child_attempts_paged() must pass offset to the repository,
      not fetch 200 rows and slice in Python.
      """
      from unittest.mock import AsyncMock, patch
      from uuid import uuid4
      from app.modules.user.parent_service import parent_service

      parent_id = uuid4()
      child_id = uuid4()
      mock_db = AsyncMock()

      # Mock the repo to return 10 fake rows and count=25
      fake_rows = [{"attempt_id": str(uuid4()), "exam_title_en": f"Exam {i}"} for i in range(10)]

      # The service uses child_repo.get_by_id for ownership (ADR-013 flow)
      with patch(
          'app.modules.user.parent_service.parent_repository.get_child_attempts',
          new_callable=AsyncMock,
          return_value=fake_rows,
      ) as mock_attempts, patch(
          'app.modules.user.parent_service.parent_repository.get_child_attempts_count',
          new_callable=AsyncMock,
          return_value=25,
      ) as mock_count, patch(
          'app.modules.user.parent_service.child_repository.get_by_id',
          new_callable=AsyncMock,
          return_value={"id": str(child_id), "parent_id": str(parent_id)},
      ):
          result = await parent_service.get_child_attempts_paged(
              mock_db, parent_id, child_id, page=2, page_size=10
          )

      # Must pass offset=10 to the repo (page 2, size 10 → skip first 10)
      mock_attempts.assert_called_once()
      call_kwargs = mock_attempts.call_args.kwargs
      assert call_kwargs.get('offset') == 10, f"Expected offset=10, got {call_kwargs}"
      assert call_kwargs.get('limit') == 10

      # Result must include pagination metadata.
      # Key is "size" (not "page_size") to preserve existing API contract with frontend.
      assert result['total'] == 25
      assert result['page'] == 2
      assert result['size'] == 10
      assert len(result['items']) == 10


  @pytest.mark.asyncio
  async def test_get_child_attempts_count_exists_in_repository():
      """parent_repository must have get_child_attempts_count method."""
      from app.modules.user.parent_repository import parent_repository
      assert hasattr(parent_repository, 'get_child_attempts_count'), (
          "parent_repository must define get_child_attempts_count(db, child_profile_id) -> int"
      )
  ```

- [ ] **Step 3: Run tests to verify they fail**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/modules/user/tests/test_parent_service.py::test_get_child_attempts_paged_uses_sql_offset_not_python_slice backend/app/modules/user/tests/test_parent_service.py::test_get_child_attempts_count_exists_in_repository -v
  ```
  Expected: Both `FAILED`.

- [ ] **Step 4: Add `offset` param and `get_child_attempts_count` to parent_repository.py**

  In `parent_repository.get_child_attempts()`, change the signature and SQL:

  ```python
  async def get_child_attempts(
      self,
      db: AsyncSession,
      child_profile_id: uuid.UUID,
      limit: int = 20,
      offset: int = 0,       # ← ADD THIS
  ) -> list:
  ```

  In the SQL query, change `LIMIT :lim` to:
  ```sql
  ORDER BY a.submitted_at DESC
  LIMIT  :lim
  OFFSET :off
  ```

  Add `"off": offset` to the params dict alongside `"lim": limit`.

  Then add the new `get_child_attempts_count` method after `get_child_attempts`:

  ```python
  async def get_child_attempts_count(
      self,
      db: AsyncSession,
      child_profile_id: uuid.UUID,
  ) -> int:
      """Total submitted attempts for a child — used for pagination metadata."""
      result = await db.execute(
          text("""
              SELECT COUNT(*)
              FROM attempts a
              WHERE a.child_profile_id = :cid
              AND   a.status = 'submitted'
          """),
          {"cid": str(child_profile_id)},
      )
      return result.scalar() or 0
  ```

  **Note:** The `parent_repository` singleton must be exported at the bottom of `parent_repository.py` if it isn't already. Check with:
  ```bash
  grep -n "^parent_repository = " backend/app/modules/user/parent_repository.py
  ```

- [ ] **Step 5: Fix parent_service.get_child_attempts_paged()**

  Find the `get_child_attempts_paged` method in `parent_service.py`. Replace the current implementation with:

  ```python
  async def get_child_attempts_paged(
      self,
      db: AsyncSession,
      parent_id: uuid.UUID,
      child_profile_id: uuid.UUID,
      page: int = 1,
      page_size: int = 10,
  ) -> dict:
      """Paginated attempt history for a child profile. Ownership verified via child_repo (ADR-013)."""
      # Verify parent owns this child_profile (ADR-013 flow uses child_repo, not parent_repository)
      child = await child_repository.get_by_id(child_profile_id, parent_id, db)
      if not child:
          raise Forbidden("You are not linked to this child profile")

      offset = (page - 1) * page_size

      # Both calls use the same session — do NOT use asyncio.gather (session not concurrency-safe)
      rows = await parent_repository.get_child_attempts(
          db, child_profile_id, limit=page_size, offset=offset
      )
      total = await parent_repository.get_child_attempts_count(db, child_profile_id)

      return {
          "items": [dict(r) for r in rows],
          "total": total,
          "page": page,
          "size": page_size,   # key is "size" — preserves existing API contract with frontend
      }
  ```

  **Note:** Remove any Python slice logic (`rows[start:end]`) that existed before.

- [ ] **Step 6: Run tests to verify they pass**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/modules/user/tests/test_parent_service.py -v --tb=short
  ```
  Expected: All tests pass including the 2 new ones.

- [ ] **Step 7: Commit**

  ```bash
  git add backend/app/modules/user/parent_repository.py \
          backend/app/modules/user/parent_service.py \
          backend/app/modules/user/tests/test_parent_service.py
  git commit -m "fix: SQL-level pagination for child attempts (add offset + COUNT, remove Python slice)"
  ```

---

## Task 3: P3 — LIMIT guard in wrong_answers.py

**Problem:** `build_wrong_answers_summary()` injects `limit` into a raw SQL f-string with no runtime type check. A non-integer value is a SQL injection vector.

**Files:**
- Modify: `backend/app/modules/analysis/wrong_answers.py`
- Test: `backend/app/modules/analysis/tests/test_wrong_answers.py` (create if not exists)

- [ ] **Step 1: Read wrong_answers.py**

  Read `backend/app/modules/analysis/wrong_answers.py` to find the exact line where the f-string LIMIT is used and where the guard should be inserted.

- [ ] **Step 2: Write the failing tests**

  Create or append to `backend/app/modules/analysis/tests/test_wrong_answers.py`:

  ```python
  """Tests for wrong_answers.py LIMIT parameter guard."""
  import pytest
  from unittest.mock import AsyncMock, MagicMock, patch


  @pytest.mark.asyncio
  async def test_limit_string_raises_bad_request():
      """A string limit value must raise BadRequest, not reach the SQL."""
      from app.modules.analysis.wrong_answers import build_wrong_answers_summary
      from app.shared.exceptions import BadRequest
      from uuid import uuid4

      mock_db = AsyncMock()
      with pytest.raises(BadRequest, match="limit must be a positive integer"):
          await build_wrong_answers_summary(
              attempt_id=uuid4(),
              db=mock_db,
              limit="DROP TABLE users",
          )


  @pytest.mark.asyncio
  async def test_limit_zero_raises_bad_request():
      """A limit of 0 must raise BadRequest."""
      from app.modules.analysis.wrong_answers import build_wrong_answers_summary
      from app.shared.exceptions import BadRequest
      from uuid import uuid4

      mock_db = AsyncMock()
      with pytest.raises(BadRequest, match="limit must be a positive integer"):
          await build_wrong_answers_summary(
              attempt_id=uuid4(),
              db=mock_db,
              limit=0,
          )


  @pytest.mark.asyncio
  async def test_limit_negative_raises_bad_request():
      """A negative limit must raise BadRequest."""
      from app.modules.analysis.wrong_answers import build_wrong_answers_summary
      from app.shared.exceptions import BadRequest
      from uuid import uuid4

      mock_db = AsyncMock()
      with pytest.raises(BadRequest, match="limit must be a positive integer"):
          await build_wrong_answers_summary(
              attempt_id=uuid4(),
              db=mock_db,
              limit=-5,
          )


  @pytest.mark.asyncio
  async def test_limit_none_does_not_raise():
      """limit=None is valid — means 'return all'. Must not raise BadRequest."""
      from app.modules.analysis.wrong_answers import build_wrong_answers_summary
      from uuid import uuid4

      mock_db = AsyncMock()
      # Mock the DB to return no attempt row (will return empty summary)
      mock_db.execute.return_value.mappings.return_value.first.return_value = None

      # Should not raise — may return empty WrongAnswersSummary
      try:
          await build_wrong_answers_summary(
              attempt_id=uuid4(),
              db=mock_db,
              limit=None,
          )
      except Exception as e:
          from app.shared.exceptions import BadRequest
          assert not isinstance(e, BadRequest), f"limit=None should not raise BadRequest, got: {e}"
  ```

- [ ] **Step 3: Run tests to verify they fail**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/modules/analysis/tests/test_wrong_answers.py -v --tb=short
  ```
  Expected: First 3 tests `FAILED` (no BadRequest raised). 4th test may pass or fail depending on DB mocks.

- [ ] **Step 4: Add the guard to wrong_answers.py**

  In `backend/app/modules/analysis/wrong_answers.py`, find the function signature for `build_wrong_answers_summary`. Add the guard as the **first lines of the function body**, before any DB calls:

  ```python
  async def build_wrong_answers_summary(
      attempt_id: uuid.UUID,
      db: AsyncSession,
      include_details: bool = True,
      limit: Optional[int] = None,
  ) -> WrongAnswersSummary:
      # Guard: limit must be a positive integer if provided
      if limit is not None and (not isinstance(limit, int) or limit < 1):
          from app.shared.exceptions import BadRequest
          raise BadRequest("limit must be a positive integer")

      # ... rest of existing function body unchanged ...
  ```

- [ ] **Step 5: Run tests to verify they pass**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/modules/analysis/tests/test_wrong_answers.py -v --tb=short
  ```
  Expected: `4 passed` (or 3 passed + 1 passed for the None case).

- [ ] **Step 6: Run full test suite**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/ -v --tb=short 2>&1 | tail -20
  ```
  Expected: All tests pass.

- [ ] **Step 7: Commit**

  ```bash
  git add backend/app/modules/analysis/wrong_answers.py \
          backend/app/modules/analysis/tests/test_wrong_answers.py
  git commit -m "fix: add type guard for limit param in wrong_answers to prevent SQL injection"
  ```

---

## Task 4: Open PR

- [ ] **Step 1: Run full test suite one final time**

  ```bash
  DEBUG=true PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/ -v --tb=short 2>&1 | tail -20
  ```
  Expected: All tests pass.

- [ ] **Step 2: Open PR**

  ```bash
  gh pr create \
    --title "fix: parent/child module — singleton pattern, SQL pagination, LIMIT guard" \
    --body "Fixes P1–P3 from the production readiness audit. See docs/superpowers/specs/2026-04-07-production-readiness-cleanup-design.md" \
    --base main
  ```
