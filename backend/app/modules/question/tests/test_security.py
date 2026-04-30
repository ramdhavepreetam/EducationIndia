"""
Question module security tests — ADR-012 compliance.

THESE ARE THE MOST CRITICAL TESTS IN THE MODULE.
They verify the security boundary around correct_option.

Run: pytest backend/app/modules/question/tests/test_security.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.modules.question.schemas import (
    QuestionDeliverySchema,
    QuestionReviewSchema,
)
from app.modules.question.service import QuestionService
from app.shared.exceptions import Forbidden


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def service_with_mocks():
    mock_repo = AsyncMock()
    mock_catalog_svc = AsyncMock()
    svc = QuestionService()
    with (
        patch("app.modules.question.service.question_repository", mock_repo),
        patch("app.modules.question.service.catalog_service", mock_catalog_svc),
    ):
        yield svc, mock_repo, mock_catalog_svc


def make_delivery_question(question_no=1) -> QuestionDeliverySchema:
    return QuestionDeliverySchema(
        id=question_no,
        exam_id=1,
        section_id=1,
        topic_id=1,
        context_id=None,
        question_no=question_no,
        question_type="text",
        text_en="Sample question?",
        text_mr=None,
        question_image_url=None,
        question_image_alt_en=None,
        question_image_alt_mr=None,
        is_multi_select=False,
        marks=2,
        difficulty="medium",
        tags=[],
        options=[],
        context=None,
    )


# ── Security Test 1: Delivery never returns correct_option ────────────────────

class TestDeliveryNeverReturnsCorrectOption:
    """
    CRITICAL: This test verifies the primary ADR-012 security boundary.
    If this test fails, students can cheat by reading the API response.
    """

    async def test_delivery_schema_has_no_correct_option_field(self, service_with_mocks, mock_db):
        """QuestionDeliverySchema must not have correct_option as a field."""
        svc, repo, catalog_svc = service_with_mocks
        catalog_svc.get_active_exam.return_value = MagicMock(id=1)
        repo.fetch_by_exam_id.return_value = [make_delivery_question()]

        result = await svc.get_questions_for_exam(mock_db, exam_id=1)

        assert len(result) == 1
        q = result[0]

        # These fields must NOT exist on the delivery schema
        assert not hasattr(q, "correct_option"), (
            "SECURITY VIOLATION: correct_option found in delivery response!"
        )
        assert not hasattr(q, "explanation_en"), (
            "SECURITY VIOLATION: explanation_en found in delivery response!"
        )
        assert not hasattr(q, "explanation_mr"), (
            "SECURITY VIOLATION: explanation_mr found in delivery response!"
        )
        assert not hasattr(q, "hint_en"), (
            "SECURITY VIOLATION: hint_en found in delivery response!"
        )
        assert not hasattr(q, "hint_mr"), (
            "SECURITY VIOLATION: hint_mr found in delivery response!"
        )

    async def test_delivery_json_has_no_correct_option_field(self, service_with_mocks, mock_db):
        """Serialized JSON from delivery schema must not contain correct_option key."""
        svc, repo, catalog_svc = service_with_mocks
        catalog_svc.get_active_exam.return_value = MagicMock(id=1)
        repo.fetch_by_exam_id.return_value = [make_delivery_question()]

        result = await svc.get_questions_for_exam(mock_db, exam_id=1)
        serialized = result[0].model_dump()

        assert "correct_option" not in serialized, (
            "SECURITY VIOLATION: correct_option in serialized delivery JSON!"
        )
        assert "explanation_en" not in serialized
        assert "explanation_mr" not in serialized

    async def test_multiple_questions_none_have_correct_option(self, service_with_mocks, mock_db):
        """Security check across all 75 questions in an exam."""
        svc, repo, catalog_svc = service_with_mocks
        catalog_svc.get_active_exam.return_value = MagicMock(id=1)
        questions = [make_delivery_question(i) for i in range(1, 76)]
        repo.fetch_by_exam_id.return_value = questions

        result = await svc.get_questions_for_exam(mock_db, exam_id=1)

        for q in result:
            serialized = q.model_dump()
            assert "correct_option" not in serialized, (
                f"SECURITY VIOLATION: Q{q.question_no} has correct_option!"
            )


# ── Security Test 2: Review blocked for ongoing attempt ───────────────────────

class TestReviewBlockedForOngoingAttempt:
    """
    Students must not be able to see correct answers during an active exam.
    """

    STUDENT_ID = uuid4()
    ATTEMPT_ID = uuid4()

    async def test_review_endpoint_blocked_for_ongoing_attempt(self, service_with_mocks, mock_db):
        """Ongoing attempt → 403 Forbidden, no question data returned."""
        svc, repo, _ = service_with_mocks
        repo.get_attempt_status.return_value = {
            "status": "ongoing",
            "student_id": str(self.STUDENT_ID),
        }

        with pytest.raises(Forbidden) as exc_info:
            await svc.get_question_for_review(
                mock_db,
                question_id=1,
                attempt_id=self.ATTEMPT_ID,
                student_id=self.STUDENT_ID,
            )

        # Verify fetch_by_id_for_review was NEVER called
        repo.fetch_by_id_for_review.assert_not_called()

        # Verify error message is informative
        assert "submitting" in str(exc_info.value.detail).lower() or \
               "submitted" in str(exc_info.value.detail).lower()

    async def test_review_blocked_for_abandoned_attempt(self, service_with_mocks, mock_db):
        """Abandoned attempts also cannot access correct answers (only submitted can)."""
        svc, repo, _ = service_with_mocks
        repo.get_attempt_status.return_value = {
            "status": "abandoned",
            "student_id": str(self.STUDENT_ID),
        }

        with pytest.raises(Forbidden):
            await svc.get_question_for_review(
                mock_db,
                question_id=1,
                attempt_id=self.ATTEMPT_ID,
                student_id=self.STUDENT_ID,
            )

    async def test_review_blocked_for_expired_attempt(self, service_with_mocks, mock_db):
        """Expired attempts (time ran out) cannot access correct answers."""
        svc, repo, _ = service_with_mocks
        repo.get_attempt_status.return_value = {
            "status": "expired",
            "student_id": str(self.STUDENT_ID),
        }

        with pytest.raises(Forbidden):
            await svc.get_question_for_review(
                mock_db,
                question_id=1,
                attempt_id=self.ATTEMPT_ID,
                student_id=self.STUDENT_ID,
            )

    async def test_review_allowed_for_submitted_attempt(self, service_with_mocks, mock_db):
        """Only submitted attempts can access review."""
        svc, repo, _ = service_with_mocks
        repo.get_attempt_status.return_value = {
            "status": "submitted",
            "student_id": str(self.STUDENT_ID),
        }
        mock_review = MagicMock(spec=QuestionReviewSchema)
        repo.fetch_by_id_for_review.return_value = mock_review

        result = await svc.get_question_for_review(
            mock_db,
            question_id=1,
            attempt_id=self.ATTEMPT_ID,
            student_id=self.STUDENT_ID,
        )
        assert result == mock_review


# ── Security Test 3: Attempt ownership ───────────────────────────────────────

class TestReviewBlockedForWrongStudent:
    """A student must not be able to review another student's attempt."""

    STUDENT_A = uuid4()
    STUDENT_B = uuid4()
    ATTEMPT_ID = uuid4()

    async def test_review_endpoint_blocked_for_wrong_student(self, service_with_mocks, mock_db):
        """Student B cannot access Student A's attempt, even if submitted."""
        svc, repo, _ = service_with_mocks
        repo.get_attempt_status.return_value = {
            "status": "submitted",
            "student_id": str(self.STUDENT_A),  # belongs to A
        }

        with pytest.raises(Forbidden, match="belong to you"):
            await svc.get_question_for_review(
                mock_db,
                question_id=1,
                attempt_id=self.ATTEMPT_ID,
                student_id=self.STUDENT_B,  # B is requesting
            )

        # Review data must never be fetched
        repo.fetch_by_id_for_review.assert_not_called()


# ── Security Test 4: Delivery schema immutability check ──────────────────────

class TestDeliverySchemaFields:
    """
    Static checks on QuestionDeliverySchema to prevent accidental field additions.
    If someone adds correct_option to the schema, this test catches it immediately.
    """

    def test_delivery_schema_field_allowlist(self):
        """Exhaustive check — these are the ONLY fields delivery schema may have."""
        allowed_fields = {
            "id", "exam_id", "section_id", "topic_id", "context_id",
            "question_no", "question_type", "text_en", "text_mr",
            "question_image_url", "question_image_alt_en", "question_image_alt_mr",
            "is_multi_select", "marks", "difficulty", "tags", "options", "context",
        }
        forbidden_fields = {
            "correct_option", "explanation_en", "explanation_mr",
            "hint_en", "hint_mr", "is_correct", "actual_difficulty_ratio",
        }

        schema_fields = set(QuestionDeliverySchema.model_fields.keys())

        for field in forbidden_fields:
            assert field not in schema_fields, (
                f"SECURITY VIOLATION: '{field}' must not be in QuestionDeliverySchema"
            )

        unexpected = schema_fields - allowed_fields
        assert not unexpected, (
            f"Unexpected fields in QuestionDeliverySchema: {unexpected}. "
            "Update this test's allowlist if the addition is intentional."
        )
