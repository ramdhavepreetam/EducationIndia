"""
Unit tests for ParentRepository.

Mocks AsyncSession so no real database is needed.
Each test covers one method's success or failure path.

Note: SQL WHERE clauses (e.g. is_active=True, role='student') are part of the
query sent to the DB — with a mocked session we verify the repository correctly
returns whatever the DB gives back. The SQL correctness is validated by
integration tests or by inspecting the query text in the implementation.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.user.models import ParentStudentLink, UserProfile
from app.modules.user.parent_repository import ParentRepository
from app.shared.exceptions import Forbidden

pytestmark = pytest.mark.asyncio


@pytest.fixture
def repo():
    return ParentRepository()


@pytest.fixture
def db():
    return AsyncMock()


# ── get_linked_children ────────────────────────────────────────────────────────

class TestGetLinkedChildren:
    async def test_returns_only_active_links(self, repo, db):
        """
        Repo returns whatever the DB query produces.
        DB query already filters is_active=True in the WHERE clause.
        Simulate: DB returns 2 rows (active links only, inactive filtered out).
        """
        parent_id = uuid4()
        row1 = MagicMock()
        row2 = MagicMock()

        mock_result = MagicMock()
        mock_result.all.return_value = [row1, row2]
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_linked_children(db, parent_id)

        assert len(result) == 2
        db.execute.assert_awaited_once()

    async def test_returns_empty_list_when_no_children(self, repo, db):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_linked_children(db, uuid4())

        assert result == []


# ── get_link ───────────────────────────────────────────────────────────────────

class TestGetLink:
    async def test_returns_none_for_missing_link(self, repo, db):
        """No row at all between parent + student."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_link(db, uuid4(), uuid4())

        assert result is None

    async def test_returns_none_for_inactive_link(self, repo, db):
        """
        The WHERE clause filters is_active=True.
        DB returns None when the link exists but is inactive.
        """
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # DB filtered it out
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_link(db, uuid4(), uuid4())

        assert result is None

    async def test_returns_link_when_active(self, repo, db):
        parent_id = uuid4()
        student_id = uuid4()
        active_link = MagicMock(spec=ParentStudentLink)
        active_link.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = active_link
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_link(db, parent_id, student_id)

        assert result is active_link


# ── find_student_by_email ──────────────────────────────────────────────────────

class TestFindStudentByEmail:
    async def test_returns_none_when_not_found(self, repo, db):
        """Email not registered or role is not 'student' — DB returns None."""
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = None
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.find_student_by_email(db, "admin@example.com")

        assert result is None

    async def test_excludes_admins(self, repo, db):
        """
        The raw SQL includes AND up.role = 'student'.
        If the email belongs to an admin, the DB returns no row.
        Simulate: DB returns None (admin filtered out by WHERE clause).
        """
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = None
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.find_student_by_email(db, "examadmin@example.com")

        assert result is None
        # Confirm a SQL query was executed (not skipped)
        db.execute.assert_awaited_once()

    async def test_returns_student_row_when_found(self, repo, db):
        student_row = {"id": uuid4(), "full_name": "Arjun S", "std_class": 5,
                       "school_name": "City School", "is_active": True}
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = student_row
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.find_student_by_email(db, "arjun@example.com")

        assert result is student_row


# ── create_link ────────────────────────────────────────────────────────────────

class TestCreateLink:
    async def test_sets_is_active_true(self, repo, db):
        """Newly created link must always be active."""
        parent_id = uuid4()
        student_id = uuid4()
        db.flush = AsyncMock()

        result = await repo.create_link(db, parent_id, student_id, parent_id)

        assert result.is_active is True

    async def test_adds_link_to_session(self, repo, db):
        db.flush = AsyncMock()

        await repo.create_link(db, uuid4(), uuid4(), uuid4())

        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    async def test_link_has_correct_parent_and_student(self, repo, db):
        parent_id = uuid4()
        student_id = uuid4()
        db.flush = AsyncMock()

        result = await repo.create_link(db, parent_id, student_id, parent_id)

        assert result.parent_id == parent_id
        assert result.student_id == student_id


# ── deactivate_link ────────────────────────────────────────────────────────────

class TestDeactivateLink:
    async def test_returns_false_if_not_found(self, repo, db):
        """No matching row → rowcount=0 → returns False."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.deactivate_link(db, uuid4(), uuid4())

        assert result is False

    async def test_returns_true_if_row_updated(self, repo, db):
        mock_result = MagicMock()
        mock_result.rowcount = 1
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.deactivate_link(db, uuid4(), uuid4())

        assert result is True


# ── update_nickname ────────────────────────────────────────────────────────────

class TestUpdateNickname:
    async def test_returns_false_if_no_active_link(self, repo, db):
        mock_result = MagicMock()
        mock_result.rowcount = 0
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.update_nickname(db, uuid4(), uuid4(), "Buddy")

        assert result is False

    async def test_returns_true_on_success(self, repo, db):
        mock_result = MagicMock()
        mock_result.rowcount = 1
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.update_nickname(db, uuid4(), uuid4(), "Buddy")

        assert result is True


# ── get_child_stats ────────────────────────────────────────────────────────────

class TestGetChildStats:
    async def test_returns_defaults_if_no_attempts(self, repo, db):
        """COUNT(*) returns 0 when no submitted attempts — safe defaults returned."""
        mock_row = {"total_attempts": 0, "avg_percentage": None,
                    "best_score": None, "best_percentage": None,
                    "last_active": None, "exams_completed": 0}
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = mock_row
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_child_stats(db, uuid4())

        assert result["total_attempts"] == 0
        assert result["avg_percentage"] is None
        assert result["best_score"] is None
        assert result["exams_completed"] == 0

    async def test_returns_defaults_when_row_is_none(self, repo, db):
        """Defensive: if DB somehow returns None row, still return safe dict."""
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = None
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_child_stats(db, uuid4())

        assert result["total_attempts"] == 0

    async def test_returns_stats_when_attempts_exist(self, repo, db):
        mock_row = {"total_attempts": 5, "avg_percentage": 72.4,
                    "best_score": 130, "best_percentage": 86.7,
                    "last_active": "2025-03-01", "exams_completed": 2}
        mock_mappings = MagicMock()
        mock_mappings.first.return_value = mock_row
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_child_stats(db, uuid4())

        assert result["total_attempts"] == 5
        assert result["avg_percentage"] == 72.4
        assert result["best_score"] == 130


# ── get_child_attempts ─────────────────────────────────────────────────────────

class TestGetChildAttempts:
    async def test_raises_forbidden_if_not_linked(self, repo, db):
        """
        Parent without an active link to this student must get 403 Forbidden.
        The link check fires before any attempt query.
        """
        with patch.object(repo, "get_link", new_callable=AsyncMock) as mock_get_link:
            mock_get_link.return_value = None

            with pytest.raises(Forbidden):
                await repo.get_child_attempts(db, uuid4(), uuid4())

        # No attempt query should have fired
        db.execute.assert_not_awaited()

    async def test_returns_attempts_when_linked(self, repo, db):
        """When link exists the repo forwards DB rows to caller."""
        active_link = MagicMock(spec=ParentStudentLink)
        active_link.is_active = True

        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings

        with patch.object(repo, "get_link", new_callable=AsyncMock) as mock_get_link:
            mock_get_link.return_value = active_link
            db.execute = AsyncMock(return_value=mock_result)

            result = await repo.get_child_attempts(db, uuid4(), uuid4())

        assert len(result) == 2


# ── get_child_topic_performance ────────────────────────────────────────────────

class TestGetChildTopicPerformance:
    async def test_returns_empty_list_when_no_data(self, repo, db):
        mock_mappings = MagicMock()
        mock_mappings.all.return_value = []
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_child_topic_performance(db, uuid4())

        assert result == []

    async def test_returns_list_of_dicts(self, repo, db):
        row1 = MagicMock()
        row1.__iter__ = MagicMock(return_value=iter([
            ("topic_id", 3), ("topic_name_en", "Fractions"),
            ("topic_name_mr", None), ("avg_percentage", 42.0),
            ("attempts_count", 3), ("status", "weak"),
        ]))
        row1.keys = MagicMock(return_value=["topic_id", "topic_name_en",
                                            "topic_name_mr", "avg_percentage",
                                            "attempts_count", "status"])

        # Simpler: use a plain dict for the mapping row
        row_data = {"topic_id": 3, "topic_name_en": "Fractions",
                    "topic_name_mr": None, "avg_percentage": 42.0,
                    "attempts_count": 3, "status": "weak"}

        mock_mappings = MagicMock()
        mock_mappings.all.return_value = [row_data]
        mock_result = MagicMock()
        mock_result.mappings.return_value = mock_mappings
        db.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_child_topic_performance(db, uuid4())

        assert len(result) == 1
        assert result[0]["topic_name_en"] == "Fractions"
        assert result[0]["status"] == "weak"
