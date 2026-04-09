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
