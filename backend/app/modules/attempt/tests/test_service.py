"""
Attempt module service unit tests.

Repository and catalog_service are mocked — no DB required.
Tests focus on business logic: validation, ownership, timer, state transitions.

Run: pytest backend/app/modules/attempt/tests/test_service.py -v
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.modules.attempt.schemas import (
    AttemptResultResponse,
    AttemptStateResponse,
    ResponseStateItem,
    SaveResponseRequest,
    StartAttemptRequest,
)
from app.modules.attempt.service import AttemptService
from app.modules.attempt.state_machine import AttemptAlreadySubmittedException
from app.shared.exceptions import BadRequest, Conflict, Forbidden, NotFound


# ── Fixtures ──────────────────────────────────────────────────────────────────

STUDENT_ID = uuid4()
OTHER_STUDENT_ID = uuid4()
ATTEMPT_ID = uuid4()
EXAM_ID = 1


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_catalog():
    svc = AsyncMock()
    exam = MagicMock()
    exam.id = EXAM_ID
    exam.duration_minutes = 90
    svc.get_active_exam.return_value = exam
    svc.get_exam.return_value = exam
    return svc


@pytest.fixture
def service(mock_repo, mock_catalog):
    svc = AttemptService()
    with (
        patch("app.modules.attempt.service.attempt_repository", mock_repo),
        patch("app.modules.attempt.service.catalog_service", mock_catalog),
    ):
        yield svc, mock_repo, mock_catalog


def make_attempt(
    status="ongoing",
    student_id=STUDENT_ID,
    started_at=None,
):
    """Create a minimal mock Attempt with sensible defaults."""
    import types
    a = MagicMock()
    a.id = ATTEMPT_ID
    a.exam_id = EXAM_ID
    a.student_id = student_id
    a.attempt_number = 1
    # Simulate AttemptStatusEnum: .value returns the string
    status_obj = types.SimpleNamespace(value=status)
    a.status = status_obj
    a.started_at = started_at or datetime.now(timezone.utc)
    a.submitted_at = None
    a.total_score = 10
    a.total_correct = 5
    a.total_wrong = 3
    a.total_skipped = 2
    a.percentage = 13.33
    a.grade = "Below Average"
    a.section_scores = []
    a.topic_scores = []
    a.time_analysis = {}
    a.recommendations = []
    return a


def make_response(question_id=1, question_no=1, selected_option=2):
    r = MagicMock()
    r.question_id = question_id
    r.question_no = question_no
    r.selected_option = selected_option
    r.is_marked_review = False
    r.visit_count = 1
    return r


# ── start_exam ────────────────────────────────────────────────────────────────

class TestStartExam:
    async def test_creates_attempt_successfully(self, service, mock_db):
        svc, repo, catalog = service
        repo.get_ongoing_attempt.return_value = None
        repo.get_attempt_number.return_value = 1
        created = make_attempt()
        repo.create_attempt.return_value = created

        result = await svc.start_exam(mock_db, STUDENT_ID, StartAttemptRequest(exam_id=EXAM_ID))

        assert isinstance(result, AttemptStateResponse)
        assert result.attempt_id == ATTEMPT_ID
        assert result.responses == []
        assert result.time_remaining_seconds == 90 * 60

    async def test_fails_if_ongoing_attempt_exists(self, service, mock_db):
        svc, repo, catalog = service
        repo.get_ongoing_attempt.return_value = make_attempt()

        with pytest.raises(Conflict, match="already have an ongoing attempt"):
            await svc.start_exam(mock_db, STUDENT_ID, StartAttemptRequest(exam_id=EXAM_ID))

        repo.create_attempt.assert_not_called()

    async def test_calls_catalog_to_validate_exam(self, service, mock_db):
        svc, repo, catalog = service
        repo.get_ongoing_attempt.return_value = None
        repo.get_attempt_number.return_value = 1
        repo.create_attempt.return_value = make_attempt()

        await svc.start_exam(mock_db, STUDENT_ID, StartAttemptRequest(exam_id=EXAM_ID))

        catalog.get_active_exam.assert_called_once_with(mock_db, EXAM_ID)

    async def test_raises_not_found_for_inactive_exam(self, service, mock_db):
        svc, repo, catalog = service
        catalog.get_active_exam.side_effect = NotFound("Exam not available")

        with pytest.raises(NotFound):
            await svc.start_exam(mock_db, STUDENT_ID, StartAttemptRequest(exam_id=EXAM_ID))


# ── save_response ─────────────────────────────────────────────────────────────

class TestSaveResponse:
    async def test_save_response_returns_state_item(self, service, mock_db):
        svc, repo, catalog = service
        attempt = make_attempt()
        repo.get_attempt_by_id.return_value = attempt
        response = make_response()
        repo.upsert_response.return_value = response

        with patch.object(svc, "_get_question_no", AsyncMock(return_value=1)):
            result = await svc.save_response(
                mock_db, ATTEMPT_ID, STUDENT_ID,
                SaveResponseRequest(question_id=1, selected_option=2)
            )

        assert isinstance(result, ResponseStateItem)
        assert result.visit_count == 1

    async def test_fails_if_attempt_belongs_to_other_student(self, service, mock_db):
        svc, repo, catalog = service
        attempt = make_attempt(student_id=OTHER_STUDENT_ID)
        repo.get_attempt_by_id.return_value = attempt

        with pytest.raises(Forbidden, match="belong to you"):
            await svc.save_response(
                mock_db, ATTEMPT_ID, STUDENT_ID,
                SaveResponseRequest(question_id=1, selected_option=2)
            )

    async def test_fails_if_attempt_is_submitted(self, service, mock_db):
        svc, repo, catalog = service
        attempt = make_attempt(status="submitted")
        repo.get_attempt_by_id.return_value = attempt

        with pytest.raises(AttemptAlreadySubmittedException):
            await svc.save_response(
                mock_db, ATTEMPT_ID, STUDENT_ID,
                SaveResponseRequest(question_id=1, selected_option=2)
            )

    async def test_fails_if_attempt_is_expired(self, service, mock_db):
        svc, repo, catalog = service
        attempt = make_attempt(status="expired")
        repo.get_attempt_by_id.return_value = attempt

        with pytest.raises(Forbidden, match="expired"):
            await svc.save_response(
                mock_db, ATTEMPT_ID, STUDENT_ID,
                SaveResponseRequest(question_id=1, selected_option=2)
            )


# ── submit_exam ───────────────────────────────────────────────────────────────

# Scoring was moved to analysis_service.generate_report (ADR-006).
# Tests patch analysis_service.generate_report instead of the old _compute_result_stub.

_SCORE_RESULT = {
    "total_score": 0,
    "total_correct": 0,
    "total_wrong": 0,
    "total_skipped": 75,
    "percentage": 0.0,
    "grade": "Below Average",
    "section_scores": [],
    "topic_scores": [],
    "time_analysis": {},
    "recommendations": [],
}


class TestSubmitExam:
    async def test_submit_transitions_to_submitted(self, service, mock_db):
        svc, repo, catalog = service
        attempt = make_attempt()
        repo.get_attempt_by_id.return_value = attempt
        repo.get_all_responses.return_value = []
        repo.update_attempt_result.return_value = attempt

        with patch("app.modules.attempt.service.transition", AsyncMock(return_value=attempt)):
            with patch(
                "app.modules.analysis.service.analysis_service.generate_report",
                AsyncMock(return_value=_SCORE_RESULT),
            ):
                result = await svc.submit_exam(mock_db, ATTEMPT_ID, STUDENT_ID)

        assert isinstance(result, AttemptResultResponse)

    async def test_submit_fails_for_other_student_attempt(self, service, mock_db):
        svc, repo, catalog = service
        attempt = make_attempt(student_id=OTHER_STUDENT_ID)
        repo.get_attempt_by_id.return_value = attempt

        with pytest.raises(Forbidden, match="belong to you"):
            await svc.submit_exam(mock_db, ATTEMPT_ID, STUDENT_ID)

    async def test_submit_rejected_after_grace_period(self, service, mock_db):
        """If timer expired more than 30s ago, reject submission."""
        svc, repo, catalog = service
        # started 91 minutes + 31 seconds ago (beyond grace)
        very_old_start = datetime.now(timezone.utc) - timedelta(minutes=91, seconds=31)
        attempt = make_attempt(started_at=very_old_start)
        repo.get_attempt_by_id.return_value = attempt

        with pytest.raises(BadRequest, match="expired"):
            await svc.submit_exam(mock_db, ATTEMPT_ID, STUDENT_ID)

    async def test_submit_within_grace_period_succeeds(self, service, mock_db):
        """30-second grace: 90 min + 20s elapsed should still be accepted."""
        svc, repo, catalog = service
        recent_start = datetime.now(timezone.utc) - timedelta(minutes=90, seconds=20)
        attempt = make_attempt(started_at=recent_start)
        repo.get_attempt_by_id.return_value = attempt
        repo.get_all_responses.return_value = []
        repo.update_attempt_result.return_value = attempt

        with patch("app.modules.attempt.service.transition", AsyncMock(return_value=attempt)):
            with patch(
                "app.modules.analysis.service.analysis_service.generate_report",
                AsyncMock(return_value=_SCORE_RESULT),
            ):
                result = await svc.submit_exam(mock_db, ATTEMPT_ID, STUDENT_ID)

        assert isinstance(result, AttemptResultResponse)

    async def test_result_contains_no_correct_option(self, service, mock_db):
        """Security: submit response must not contain correct_option."""
        svc, repo, catalog = service
        attempt = make_attempt()
        repo.get_attempt_by_id.return_value = attempt
        repo.get_all_responses.return_value = []
        repo.update_attempt_result.return_value = attempt

        with patch("app.modules.attempt.service.transition", AsyncMock(return_value=attempt)):
            with patch(
                "app.modules.analysis.service.analysis_service.generate_report",
                AsyncMock(return_value=_SCORE_RESULT),
            ):
                result = await svc.submit_exam(mock_db, ATTEMPT_ID, STUDENT_ID)

        result_dict = result.model_dump()
        assert "correct_option" not in result_dict
        assert "correct_option" not in str(result_dict.get("recommendations", ""))
