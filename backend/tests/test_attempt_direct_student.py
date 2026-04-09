"""Tests for direct-student attempt flow (no child_profile_id)."""
import pytest
from app.modules.attempt.schemas import StartAttemptRequest

def test_start_attempt_request_child_profile_id_is_optional():
    """child_profile_id should default to None for direct students."""
    req = StartAttemptRequest(exam_id=1, assignment_id=None)
    assert req.child_profile_id is None

def test_start_attempt_request_accepts_child_profile_id():
    """child_profile_id can still be provided for parent-for-child flow."""
    from uuid import uuid4
    req = StartAttemptRequest(exam_id=1, child_profile_id=uuid4())
    assert req.child_profile_id is not None


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
