"""
Question module service unit tests.

Tests business logic in QuestionService in isolation.
Repository is mocked with AsyncMock — no DB required.
Run: pytest backend/app/modules/question/tests/test_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from app.modules.question.schemas import (
    BulkImportSchema,
    BulkImportResult,
    ContextImportItem,
    OptionImportItem,
    QuestionDeliverySchema,
    QuestionImportItem,
    QuestionReviewSchema,
)
from app.modules.question.service import QuestionService
from app.shared.exceptions import BadRequest, Forbidden, NotFound


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_catalog_service():
    return AsyncMock()


@pytest.fixture
def service(mock_repo, mock_catalog_service):
    """QuestionService with repository and catalog_service mocked."""
    svc = QuestionService()
    with (
        patch("app.modules.question.service.question_repository", mock_repo),
        patch("app.modules.question.service.catalog_service", mock_catalog_service),
    ):
        yield svc, mock_repo, mock_catalog_service


def make_delivery_question(question_no=1, **kwargs) -> QuestionDeliverySchema:
    return QuestionDeliverySchema(
        id=kwargs.get("id", question_no),
        exam_id=kwargs.get("exam_id", 1),
        section_id=kwargs.get("section_id", 1),
        topic_id=kwargs.get("topic_id", 1),
        context_id=None,
        question_no=question_no,
        question_type="text",
        text_en="Which of the following is correct?",
        text_mr=None,
        question_image_url=None,
        question_image_alt_en=None,
        question_image_alt_mr=None,
        marks=2,
        difficulty="medium",
        tags=[],
        options=[],
        context=None,
    )


def make_import_data(exam_id=1, count=5) -> BulkImportSchema:
    questions = []
    for i in range(1, count + 1):
        questions.append(
            QuestionImportItem(
                section_id=1,
                topic_id=1,
                question_no=i,
                question_type="text",
                text_en=f"Question {i}?",
                correct_option=1,
                options=[
                    OptionImportItem(option_no=j, text_en=f"Option {j}")
                    for j in range(1, 5)
                ],
            )
        )
    return BulkImportSchema(exam_id=exam_id, questions=questions)


# ── Test: get_questions_for_exam ──────────────────────────────────────────────

class TestGetQuestionsForExam:
    async def test_returns_delivery_questions(self, service, mock_db):
        svc, repo, catalog_svc = service
        expected = [make_delivery_question(i) for i in range(1, 4)]
        catalog_svc.get_active_exam.return_value = MagicMock(id=1)
        repo.fetch_by_exam_id.return_value = expected

        result = await svc.get_questions_for_exam(mock_db, exam_id=1)

        assert result == expected
        catalog_svc.get_active_exam.assert_called_once_with(mock_db, 1)
        repo.fetch_by_exam_id.assert_called_once_with(mock_db, 1)

    async def test_get_questions_never_includes_correct_option(self, service, mock_db):
        """SECURITY: delivery schema must not have correct_option attribute."""
        svc, repo, catalog_svc = service
        catalog_svc.get_active_exam.return_value = MagicMock(id=1)
        repo.fetch_by_exam_id.return_value = [make_delivery_question()]

        result = await svc.get_questions_for_exam(mock_db, exam_id=1)

        for q in result:
            assert not hasattr(q, "correct_option"), (
                "QuestionDeliverySchema must never have correct_option"
            )
            assert not hasattr(q, "explanation_en"), (
                "QuestionDeliverySchema must never have explanation_en"
            )

    async def test_returns_empty_list_when_no_questions(self, service, mock_db):
        svc, repo, catalog_svc = service
        catalog_svc.get_active_exam.return_value = MagicMock(id=1)
        repo.fetch_by_exam_id.return_value = []

        result = await svc.get_questions_for_exam(mock_db, exam_id=1)

        assert result == []

    async def test_raises_not_found_for_inactive_exam(self, service, mock_db):
        svc, repo, catalog_svc = service
        catalog_svc.get_active_exam.side_effect = NotFound("Exam 999 is not available")

        with pytest.raises(NotFound):
            await svc.get_questions_for_exam(mock_db, exam_id=999)

        repo.fetch_by_exam_id.assert_not_called()


# ── Test: get_question_for_review ─────────────────────────────────────────────

class TestGetQuestionForReview:
    STUDENT_ID = uuid4()
    ATTEMPT_ID = uuid4()

    async def test_get_question_review_requires_submitted_attempt(self, service, mock_db):
        """Returns review schema when attempt is submitted and belongs to student."""
        svc, repo, _ = service
        repo.get_attempt_status.return_value = {
            "status": "submitted",
            "student_id": str(self.STUDENT_ID),
        }
        review = MagicMock(spec=QuestionReviewSchema)
        repo.fetch_by_id_for_review.return_value = review

        result = await svc.get_question_for_review(
            mock_db, question_id=1, attempt_id=self.ATTEMPT_ID, student_id=self.STUDENT_ID
        )

        assert result == review
        repo.fetch_by_id_for_review.assert_called_once_with(mock_db, 1)

    async def test_get_question_review_rejected_for_ongoing_attempt(self, service, mock_db):
        """SECURITY: ongoing attempt cannot access correct answers."""
        svc, repo, _ = service
        repo.get_attempt_status.return_value = {
            "status": "ongoing",
            "student_id": str(self.STUDENT_ID),
        }

        with pytest.raises(Forbidden, match="submitting"):
            await svc.get_question_for_review(
                mock_db, question_id=1, attempt_id=self.ATTEMPT_ID, student_id=self.STUDENT_ID
            )

        repo.fetch_by_id_for_review.assert_not_called()

    async def test_review_rejected_for_wrong_student(self, service, mock_db):
        """SECURITY: student cannot review another student's attempt."""
        svc, repo, _ = service
        other_student = uuid4()
        repo.get_attempt_status.return_value = {
            "status": "submitted",
            "student_id": str(other_student),
        }

        with pytest.raises(Forbidden, match="belong to you"):
            await svc.get_question_for_review(
                mock_db, question_id=1, attempt_id=self.ATTEMPT_ID, student_id=self.STUDENT_ID
            )

    async def test_review_raises_not_found_for_missing_attempt(self, service, mock_db):
        svc, repo, _ = service
        repo.get_attempt_status.return_value = None

        with pytest.raises(NotFound, match="Attempt"):
            await svc.get_question_for_review(
                mock_db, question_id=1, attempt_id=self.ATTEMPT_ID, student_id=self.STUDENT_ID
            )


# ── Test: bulk_import ─────────────────────────────────────────────────────────

class TestBulkImport:
    async def test_bulk_import_validates_question_count(self, service, mock_db):
        """Valid import batch inserts all questions."""
        svc, repo, catalog_svc = service
        catalog_svc.get_exam.return_value = MagicMock(id=1)
        import_data = make_import_data(count=5)
        repo.replace_exam_questions.return_value = (5, [])

        result = await svc.bulk_import(mock_db, import_data)

        assert result.inserted == 5
        assert result.skipped == 0
        assert result.errors == []

    async def test_bulk_import_rejects_duplicate_question_numbers(self, service, mock_db):
        """Duplicate question_no in batch raises BadRequest."""
        svc, repo, catalog_svc = service
        catalog_svc.get_exam.return_value = MagicMock(id=1)

        import_data = make_import_data(count=3)
        # Force duplicate question_no
        import_data.questions[1].question_no = 1  # duplicate of questions[0]

        with pytest.raises(BadRequest, match="Duplicate question_no"):
            await svc.bulk_import(mock_db, import_data)

        repo.replace_exam_questions.assert_not_called()

    async def test_bulk_import_raises_not_found_for_missing_exam(self, service, mock_db):
        svc, repo, catalog_svc = service
        catalog_svc.get_exam.side_effect = NotFound("Exam 999 not found")

        with pytest.raises(NotFound):
            await svc.bulk_import(mock_db, make_import_data(exam_id=999))

    async def test_bulk_import_rejects_invalid_context_ref(self, service, mock_db):
        """context_ref pointing beyond contexts array raises BadRequest."""
        svc, repo, catalog_svc = service
        catalog_svc.get_exam.return_value = MagicMock(id=1)

        import_data = make_import_data(count=1)
        import_data.questions[0].context_ref = 5  # no contexts in this batch
        import_data.contexts = []

        with pytest.raises(BadRequest, match="context_ref"):
            await svc.bulk_import(mock_db, import_data)
