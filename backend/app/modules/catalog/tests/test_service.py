"""
Catalog module service unit tests.

Tests business logic in CatalogService in isolation.
Repository is mocked with AsyncMock — no DB required.
Run: pytest backend/app/modules/catalog/tests/test_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.catalog.models import Exam, ExamBoard
from app.modules.catalog.service import CatalogService
from app.shared.exceptions import NotFound


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    """CatalogService with its repository replaced by a mock."""
    svc = CatalogService()
    with patch("app.modules.catalog.service.catalog_repository", mock_repo):
        yield svc, mock_repo


def make_board(**kwargs) -> ExamBoard:
    b = MagicMock(spec=ExamBoard)
    b.id = kwargs.get("id", 1)
    b.name_en = kwargs.get("name_en", "MSCE Maharashtra")
    b.name_mr = kwargs.get("name_mr", "महाराष्ट्र राज्य परीक्षा परिषद")
    b.short_code = kwargs.get("short_code", "MSCE")
    b.is_active = kwargs.get("is_active", True)
    return b


def make_exam(**kwargs) -> Exam:
    e = MagicMock(spec=Exam)
    e.id = kwargs.get("id", 1)
    e.title_en = kwargs.get("title_en", "Paper I — English & Mathematics")
    e.title_mr = kwargs.get("title_mr", "पेपर १")
    e.is_active = kwargs.get("is_active", True)
    e.sections = kwargs.get("sections", [])
    return e


# ── TestListBoards ────────────────────────────────────────────────────────────

class TestListBoards:
    async def test_returns_active_boards(self, service, mock_db):
        svc, repo = service
        boards = [make_board(), make_board(id=2, short_code="CBSE")]
        repo.list_active_boards.return_value = boards

        result = await svc.list_boards(mock_db)

        assert result == boards
        repo.list_active_boards.assert_called_once_with(mock_db)

    async def test_returns_empty_list_when_no_boards(self, service, mock_db):
        svc, repo = service
        repo.list_active_boards.return_value = []

        result = await svc.list_boards(mock_db)

        assert result == []


# ── TestListExams ─────────────────────────────────────────────────────────────

class TestListExams:
    async def test_students_see_active_only(self, service, mock_db):
        svc, repo = service
        repo.list_exams.return_value = [make_exam()]

        await svc.list_exams(mock_db, is_admin=False)

        repo.list_exams.assert_called_once_with(
            mock_db,
            board_id=None,
            std_class=None,
            year=None,
            include_inactive=False,
        )

    async def test_admins_see_all(self, service, mock_db):
        svc, repo = service
        repo.list_exams.return_value = [make_exam(), make_exam(id=2, is_active=False)]

        await svc.list_exams(mock_db, is_admin=True)

        repo.list_exams.assert_called_once_with(
            mock_db,
            board_id=None,
            std_class=None,
            year=None,
            include_inactive=True,
        )

    async def test_filters_forwarded_to_repository(self, service, mock_db):
        svc, repo = service
        repo.list_exams.return_value = []

        await svc.list_exams(mock_db, board_id=1, std_class=5, year=2025)

        repo.list_exams.assert_called_once_with(
            mock_db,
            board_id=1,
            std_class=5,
            year=2025,
            include_inactive=False,
        )


# ── TestGetExam ───────────────────────────────────────────────────────────────

class TestGetExam:
    async def test_returns_exam_when_found(self, service, mock_db):
        svc, repo = service
        exam = make_exam(id=1)
        repo.get_exam_by_id.return_value = exam

        result = await svc.get_exam(mock_db, exam_id=1)

        assert result == exam
        repo.get_exam_by_id.assert_called_once_with(mock_db, 1)

    async def test_raises_not_found_when_missing(self, service, mock_db):
        svc, repo = service
        repo.get_exam_by_id.return_value = None

        with pytest.raises(NotFound):
            await svc.get_exam(mock_db, exam_id=999)


# ── TestGetActiveExam ─────────────────────────────────────────────────────────

class TestGetActiveExam:
    async def test_returns_active_exam(self, service, mock_db):
        svc, repo = service
        exam = make_exam(is_active=True)
        repo.get_exam_by_id.return_value = exam

        result = await svc.get_active_exam(mock_db, exam_id=1)

        assert result == exam

    async def test_raises_not_found_for_inactive_exam(self, service, mock_db):
        svc, repo = service
        exam = make_exam(is_active=False)
        repo.get_exam_by_id.return_value = exam

        with pytest.raises(NotFound, match="not available"):
            await svc.get_active_exam(mock_db, exam_id=1)

    async def test_raises_not_found_for_missing_exam(self, service, mock_db):
        svc, repo = service
        repo.get_exam_by_id.return_value = None

        with pytest.raises(NotFound):
            await svc.get_active_exam(mock_db, exam_id=999)


# ── TestPublishExam ───────────────────────────────────────────────────────────

class TestPublishExam:
    async def test_publishes_exam(self, service, mock_db):
        svc, repo = service
        existing = make_exam(id=1, is_active=False)
        published = make_exam(id=1, is_active=True)
        repo.get_exam_by_id.return_value = existing
        repo.set_exam_active.return_value = published

        result = await svc.publish_exam(mock_db, exam_id=1)

        assert result["is_active"] is True
        assert result["exam_id"] == 1
        repo.set_exam_active.assert_called_once_with(mock_db, 1, is_active=True)

    async def test_raises_not_found_for_missing_exam(self, service, mock_db):
        svc, repo = service
        repo.get_exam_by_id.return_value = None

        with pytest.raises(NotFound):
            await svc.publish_exam(mock_db, exam_id=999)

    async def test_publishes_already_active_exam(self, service, mock_db):
        """Publishing an already-active exam is idempotent — no error."""
        svc, repo = service
        exam = make_exam(is_active=True)
        repo.get_exam_by_id.return_value = exam
        repo.set_exam_active.return_value = exam

        result = await svc.publish_exam(mock_db, exam_id=1)

        assert result["is_active"] is True
        assert result["exam_id"] == 1
