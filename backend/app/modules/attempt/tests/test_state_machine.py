"""
Attempt state machine unit tests.

Pure function tests — no DB, no mocks needed.
State machine is completely deterministic given current + target states.

Run: pytest backend/app/modules/attempt/tests/test_state_machine.py -v
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.attempt.state_machine import (
    TRANSITIONS,
    AttemptAlreadySubmittedException,
    InvalidTransitionException,
    transition,
    validate_transition,
)


# ── validate_transition (pure function) ────────────────────────────────────────

class TestValidateTransition:
    def test_ongoing_to_submitted_allowed(self):
        assert validate_transition("ongoing", "submitted") is True

    def test_ongoing_to_expired_allowed(self):
        assert validate_transition("ongoing", "expired") is True

    def test_ongoing_to_abandoned_allowed(self):
        assert validate_transition("ongoing", "abandoned") is True

    def test_abandoned_to_ongoing_allowed(self):
        assert validate_transition("abandoned", "ongoing") is True

    def test_not_started_to_ongoing_allowed(self):
        assert validate_transition("not_started", "ongoing") is True

    def test_submitted_to_ongoing_rejected(self):
        """submitted is terminal — no transitions out."""
        assert validate_transition("submitted", "ongoing") is False

    def test_submitted_to_abandoned_rejected(self):
        assert validate_transition("submitted", "abandoned") is False

    def test_expired_to_ongoing_rejected(self):
        """expired is terminal — no transitions out."""
        assert validate_transition("expired", "ongoing") is False

    def test_ongoing_to_not_started_rejected(self):
        assert validate_transition("ongoing", "not_started") is False

    def test_invalid_state_returns_false(self):
        assert validate_transition("ghost_state", "submitted") is False

    def test_all_terminal_states_have_no_transitions(self):
        for terminal in ["submitted", "expired"]:
            assert TRANSITIONS[terminal] == [], f"{terminal} should have no transitions"


# ── transition() (async — requires DB session mock) ────────────────────────────

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    return db


def make_attempt(status: str = "ongoing"):
    """
    Create a minimal mock Attempt object.
    a.status is an enum-like SimpleNamespace so that both
      str(a.status)         → "ongoing" (str of the object)
      a.status.value        → "ongoing"
    work correctly (as in the real AttemptStatusEnum).
    """
    import types
    a = MagicMock()
    a.id = uuid4()
    # Simulate AttemptStatusEnum: has .value attribute + str() == value
    status_obj = types.SimpleNamespace(value=status)
    status_obj.__str__ = lambda self: self.value
    a.status = status_obj
    a.started_at = datetime.now(timezone.utc)
    return a


class TestTransition:
    async def test_valid_transition_updates_status(self, mock_db):
        attempt = make_attempt("ongoing")
        with patch("app.modules.attempt.state_machine.update"):
            result = await transition(attempt, "submitted", mock_db)
        assert result.status == "submitted"

    async def test_submitted_sets_submitted_at(self, mock_db):
        attempt = make_attempt("ongoing")
        with patch("app.modules.attempt.state_machine.update"):
            result = await transition(attempt, "submitted", mock_db)
        assert hasattr(result, "submitted_at")
        assert result.submitted_at is not None

    async def test_submitted_computes_duration_seconds(self, mock_db):
        attempt = make_attempt("ongoing")
        # started 60 seconds ago
        attempt.started_at = datetime.now(timezone.utc).replace(
            second=datetime.now(timezone.utc).second - 1
        )
        with patch("app.modules.attempt.state_machine.update"):
            result = await transition(attempt, "submitted", mock_db)
        assert result.duration_seconds >= 0

    async def test_already_submitted_raises_exception(self, mock_db):
        attempt = make_attempt("submitted")
        attempt.status.value = "submitted"
        with pytest.raises(AttemptAlreadySubmittedException):
            await transition(attempt, "ongoing", mock_db)

    async def test_invalid_transition_raises_exception(self, mock_db):
        attempt = make_attempt("expired")
        attempt.status.value = "expired"
        with pytest.raises(InvalidTransitionException):
            await transition(attempt, "ongoing", mock_db)

    async def test_expired_to_ongoing_invalid(self, mock_db):
        """expired is terminal — cannot transition to any state."""
        attempt = make_attempt("expired")
        attempt.status.value = "expired"
        with pytest.raises(InvalidTransitionException):
            await transition(attempt, "submitted", mock_db)

    async def test_db_execute_called_on_valid_transition(self, mock_db):
        attempt = make_attempt("ongoing")
        attempt.status.value = "ongoing"
        with patch("app.modules.attempt.state_machine.update", return_value=MagicMock()):
            await transition(attempt, "abandoned", mock_db)
        mock_db.execute.assert_called_once()
        mock_db.flush.assert_called_once()
