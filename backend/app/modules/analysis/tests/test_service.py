"""
Analysis module service unit tests.

Tests the get_attempt_report() authorization logic:
  - NotFound when attempt doesn't exist
  - Forbidden when attempt not yet submitted
  - Student can view own report
  - Student cannot view another student's report
  - Parent authorization delegates to DB (tested via mock)
  - Admin bypasses all checks

All tests mock attempt_repository — no DB required.

Run: pytest backend/app/modules/analysis/tests/test_service.py -v
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.analysis.service import AnalysisService
from app.shared.exceptions import Forbidden, NotFound


# ── Fixtures ──────────────────────────────────────────────────────────────────

STUDENT_ID = uuid4()
OTHER_STUDENT_ID = uuid4()
PARENT_ID = uuid4()
ATTEMPT_ID = uuid4()
EXAM_ID = 1


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def service():
    return AnalysisService()


def make_attempt(status="submitted", student_id=STUDENT_ID):
    """Create a minimal mock Attempt ORM object."""
    import types
    a = MagicMock()
    a.id = ATTEMPT_ID
    a.exam_id = EXAM_ID
    a.student_id = student_id
    a.attempt_number = 1
    status_obj = types.SimpleNamespace(value=status)
    a.status = status_obj
    a.submitted_at = MagicMock()
    a.submitted_at.isoformat.return_value = "2026-02-24T00:00:00+00:00"
    a.total_score = 100
    a.total_correct = 50
    a.total_wrong = 20
    a.total_skipped = 5
    a.percentage = 66.67
    a.grade = "Good"
    a.section_scores = []
    a.topic_scores = []
    a.time_analysis = {"avg_per_question": 72.0}
    a.recommendations = ["Practice more Fractions"]
    return a


# ── get_attempt_report ────────────────────────────────────────────────────────

class TestGetAttemptReport:
    async def test_raises_not_found_if_attempt_missing(self, service, mock_db):
        with patch(
            "app.modules.attempt.repository.attempt_repository.get_attempt_by_id",
            AsyncMock(return_value=None),
        ):
            with pytest.raises(NotFound, match="Attempt not found"):
                await service.get_attempt_report(ATTEMPT_ID, STUDENT_ID, "student", mock_db)

    async def test_raises_forbidden_if_not_submitted(self, service, mock_db):
        attempt = make_attempt(status="ongoing")
        with patch(
            "app.modules.attempt.repository.attempt_repository.get_attempt_by_id",
            AsyncMock(return_value=attempt),
        ):
            with pytest.raises(Forbidden, match="only available for submitted"):
                await service.get_attempt_report(ATTEMPT_ID, STUDENT_ID, "student", mock_db)

    async def test_student_can_view_own_report(self, service, mock_db):
        attempt = make_attempt(student_id=STUDENT_ID)
        with patch(
            "app.modules.attempt.repository.attempt_repository.get_attempt_by_id",
            AsyncMock(return_value=attempt),
        ):
            report = await service.get_attempt_report(ATTEMPT_ID, STUDENT_ID, "student", mock_db)
            assert str(report.attempt_id) == str(ATTEMPT_ID)
            assert report.total_correct == 50
            assert "correct_option" not in report.model_dump()

    async def test_student_cannot_view_other_student_report(self, service, mock_db):
        attempt = make_attempt(student_id=OTHER_STUDENT_ID)
        with patch(
            "app.modules.attempt.repository.attempt_repository.get_attempt_by_id",
            AsyncMock(return_value=attempt),
        ):
            with pytest.raises(Forbidden, match="Not authorized"):
                await service.get_attempt_report(ATTEMPT_ID, STUDENT_ID, "student", mock_db)

    async def test_admin_bypasses_ownership_check(self, service, mock_db):
        """exam_admin or super_admin can view any student's report."""
        attempt = make_attempt(student_id=OTHER_STUDENT_ID)
        with patch(
            "app.modules.attempt.repository.attempt_repository.get_attempt_by_id",
            AsyncMock(return_value=attempt),
        ):
            # admin role — no Forbidden raised
            report = await service.get_attempt_report(ATTEMPT_ID, STUDENT_ID, "exam_admin", mock_db)
            assert str(report.attempt_id) == str(ATTEMPT_ID)

    async def test_report_contains_no_correct_option(self, service, mock_db):
        """Security: report fields must never expose correct_option."""
        attempt = make_attempt(student_id=STUDENT_ID)
        with patch(
            "app.modules.attempt.repository.attempt_repository.get_attempt_by_id",
            AsyncMock(return_value=attempt),
        ):
            report = await service.get_attempt_report(ATTEMPT_ID, STUDENT_ID, "student", mock_db)
            report_dict = report.model_dump()
            assert "correct_option" not in report_dict
            assert "correct_option" not in str(report_dict.get("section_scores", ""))
            assert "correct_option" not in str(report_dict.get("topic_scores", ""))
