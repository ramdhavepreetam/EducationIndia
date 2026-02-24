"""
Unit tests for ParentService.

Mocks parent_repository (the module-level singleton) so no real DB is needed.
Each test covers one method's success or failure path.

Patch target: app.modules.user.parent_service.parent_repository
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.user.models import ParentStudentLink, UserProfile
from app.modules.user.parent_service import ParentService
from app.shared.exceptions import BadRequest, Conflict, Forbidden, NotFound

pytestmark = pytest.mark.asyncio


# ── Factories ──────────────────────────────────────────────────────────────────

def _mock_profile(student_id=None) -> MagicMock:
    """A MagicMock shaped like a UserProfile ORM object."""
    p = MagicMock(spec=UserProfile)
    p.id = student_id or uuid4()
    p.full_name = "Arjun S"
    p.std_class = 5
    p.medium = "english"
    p.school_name = "City School"
    p.district = "Pune"
    p.avatar_url = None
    p.is_onboarded = True
    return p


def _make_child_row(student_id=None):
    """Simulate a row returned by get_linked_children: (UserProfile, nickname, linked_at)."""
    profile = _mock_profile(student_id)
    nickname = "Chhotu"
    linked_at = datetime.now(timezone.utc)
    return (profile, nickname, linked_at)


def _default_stats() -> dict:
    return {
        "total_attempts": 0,
        "avg_percentage": None,
        "best_score": None,
        "best_percentage": None,
        "last_active": None,
        "exams_completed": 0,
    }


def _mock_link() -> MagicMock:
    link = MagicMock(spec=ParentStudentLink)
    link.is_active = True
    return link


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def service():
    return ParentService()


@pytest.fixture
def db():
    db = AsyncMock()
    db.commit = AsyncMock()
    return db


PATCH = "app.modules.user.parent_service.parent_repository"


# ── get_dashboard ──────────────────────────────────────────────────────────────

class TestGetDashboard:
    async def test_returns_empty_dashboard_for_no_children(self, service, db):
        """No linked children → empty children list, no selected detail."""
        parent_id = uuid4()
        with patch(PATCH) as mock_repo:
            mock_repo.get_linked_children = AsyncMock(return_value=[])

            result = await service.get_dashboard(db, parent_id)

        assert result.children == []
        assert result.selected_child_detail is None

    async def test_loads_first_child_detail_when_children_exist(self, service, db):
        """When children exist, dashboard includes first child's detail."""
        parent_id = uuid4()
        student_id = uuid4()
        child_row = _make_child_row(student_id)

        with patch(PATCH) as mock_repo:
            mock_repo.get_linked_children = AsyncMock(return_value=[child_row])
            mock_repo.get_link = AsyncMock(return_value=_mock_link())
            mock_repo.get_child_stats = AsyncMock(return_value=_default_stats())
            mock_repo.get_child_attempts = AsyncMock(return_value=[])
            mock_repo.get_child_topic_performance = AsyncMock(return_value=[])

            result = await service.get_dashboard(db, parent_id)

        assert len(result.children) == 1
        assert result.selected_child_detail is not None
        assert result.children[0].student_id == student_id


# ── get_child_detail ───────────────────────────────────────────────────────────

class TestGetChildDetail:
    async def test_raises_forbidden_if_not_linked(self, service, db):
        """Service rejects access when no active link exists."""
        with patch(PATCH) as mock_repo:
            mock_repo.get_link = AsyncMock(return_value=None)

            with pytest.raises(Forbidden):
                await service.get_child_detail(db, uuid4(), uuid4())

    async def test_returns_full_detail_when_linked(self, service, db):
        parent_id = uuid4()
        student_id = uuid4()
        child_row = _make_child_row(student_id)

        with patch(PATCH) as mock_repo:
            mock_repo.get_link = AsyncMock(return_value=_mock_link())
            mock_repo.get_child_stats = AsyncMock(return_value=_default_stats())
            mock_repo.get_child_attempts = AsyncMock(return_value=[])
            mock_repo.get_child_topic_performance = AsyncMock(return_value=[])
            mock_repo.get_linked_children = AsyncMock(return_value=[child_row])

            result = await service.get_child_detail(db, parent_id, student_id)

        assert result.profile.student_id == student_id
        assert result.stats.total_attempts == 0

    async def test_weak_topics_split_correctly(self, service, db):
        """Topics with status=weak go to weak_topics, strong → strong_topics, average ignored."""
        parent_id = uuid4()
        student_id = uuid4()
        child_row = _make_child_row(student_id)

        topics = [
            {"topic_id": 1, "topic_name_en": "Fractions", "topic_name_mr": None,
             "avg_percentage": 42.0, "attempts_count": 3, "status": "weak"},
            {"topic_id": 2, "topic_name_en": "Grammar",   "topic_name_mr": None,
             "avg_percentage": 88.0, "attempts_count": 5, "status": "strong"},
            {"topic_id": 3, "topic_name_en": "Maps",      "topic_name_mr": None,
             "avg_percentage": 60.0, "attempts_count": 2, "status": "average"},
        ]

        with patch(PATCH) as mock_repo:
            mock_repo.get_link = AsyncMock(return_value=_mock_link())
            mock_repo.get_child_stats = AsyncMock(return_value=_default_stats())
            mock_repo.get_child_attempts = AsyncMock(return_value=[])
            mock_repo.get_child_topic_performance = AsyncMock(return_value=topics)
            mock_repo.get_linked_children = AsyncMock(return_value=[child_row])

            result = await service.get_child_detail(db, parent_id, student_id)

        assert len(result.weak_topics) == 1
        assert result.weak_topics[0].topic_name_en == "Fractions"
        assert len(result.strong_topics) == 1
        # Average topics not included in either list
        assert all(t.status != "average" for t in result.weak_topics)
        assert all(t.status != "average" for t in result.strong_topics)

    async def test_strong_topics_sorted_descending(self, service, db):
        """Strong topics sorted by avg_percentage DESC (best first)."""
        parent_id = uuid4()
        student_id = uuid4()
        child_row = _make_child_row(student_id)

        topics = [
            {"topic_id": 1, "topic_name_en": "A", "topic_name_mr": None,
             "avg_percentage": 72.0, "attempts_count": 3, "status": "strong"},
            {"topic_id": 2, "topic_name_en": "B", "topic_name_mr": None,
             "avg_percentage": 95.0, "attempts_count": 5, "status": "strong"},
        ]

        with patch(PATCH) as mock_repo:
            mock_repo.get_link = AsyncMock(return_value=_mock_link())
            mock_repo.get_child_stats = AsyncMock(return_value=_default_stats())
            mock_repo.get_child_attempts = AsyncMock(return_value=[])
            mock_repo.get_child_topic_performance = AsyncMock(return_value=topics)
            mock_repo.get_linked_children = AsyncMock(return_value=[child_row])

            result = await service.get_child_detail(db, parent_id, student_id)

        assert result.strong_topics[0].avg_percentage == 95.0
        assert result.strong_topics[1].avg_percentage == 72.0


# ── link_child ─────────────────────────────────────────────────────────────────

class TestLinkChild:
    async def test_raises_not_found_for_unknown_email(self, service, db):
        """Email not registered as student → NotFound."""
        with patch(PATCH) as mock_repo:
            mock_repo.find_student_by_email = AsyncMock(return_value=None)

            with pytest.raises(NotFound):
                await service.link_child(db, uuid4(), "unknown@test.com")

    async def test_raises_bad_request_for_self_link(self, service, db):
        """Parent tries to link their own account → BadRequest."""
        parent_id = uuid4()

        with patch(PATCH) as mock_repo:
            mock_repo.find_student_by_email = AsyncMock(
                return_value={"id": parent_id, "full_name": "Self"}
            )

            with pytest.raises(BadRequest):
                await service.link_child(db, parent_id, "self@test.com")

    async def test_raises_conflict_if_already_linked(self, service, db):
        """Active link already exists → Conflict."""
        parent_id = uuid4()
        student_id = uuid4()

        with patch(PATCH) as mock_repo:
            mock_repo.find_student_by_email = AsyncMock(
                return_value={"id": student_id, "full_name": "Arjun"}
            )
            mock_repo.get_link = AsyncMock(return_value=_mock_link())

            with pytest.raises(Conflict):
                await service.link_child(db, parent_id, "arjun@test.com")

    async def test_creates_link_and_returns_child_profile(self, service, db):
        """Happy path: link created → ChildProfileSchema returned."""
        parent_id = uuid4()
        student_id = uuid4()
        child_row = _make_child_row(student_id)

        with patch(PATCH) as mock_repo:
            mock_repo.find_student_by_email = AsyncMock(
                return_value={"id": student_id, "full_name": "Arjun"}
            )
            mock_repo.get_link = AsyncMock(return_value=None)
            mock_repo.create_link = AsyncMock(return_value=_mock_link())
            mock_repo.get_linked_children = AsyncMock(return_value=[child_row])

            result = await service.link_child(db, parent_id, "arjun@test.com")

        assert result.student_id == student_id
        mock_repo.create_link.assert_awaited_once()
        db.commit.assert_awaited_once()


# ── update_nickname ────────────────────────────────────────────────────────────

class TestUpdateNickname:
    async def test_raises_not_found_if_no_active_link(self, service, db):
        with patch(PATCH) as mock_repo:
            mock_repo.update_nickname = AsyncMock(return_value=False)

            with pytest.raises(NotFound):
                await service.update_nickname(db, uuid4(), uuid4(), "Buddy")

    async def test_returns_updated_profile_on_success(self, service, db):
        parent_id = uuid4()
        student_id = uuid4()
        child_row = _make_child_row(student_id)

        with patch(PATCH) as mock_repo:
            mock_repo.update_nickname = AsyncMock(return_value=True)
            mock_repo.get_linked_children = AsyncMock(return_value=[child_row])

            result = await service.update_nickname(
                db, parent_id, student_id, "Buddy"
            )

        assert result.student_id == student_id
        db.commit.assert_awaited_once()


# ── unlink_child ───────────────────────────────────────────────────────────────

class TestUnlinkChild:
    async def test_raises_not_found_if_no_active_link(self, service, db):
        with patch(PATCH) as mock_repo:
            mock_repo.get_link = AsyncMock(return_value=None)

            with pytest.raises(NotFound):
                await service.unlink_child(db, uuid4(), uuid4())

    async def test_returns_true_on_success(self, service, db):
        with patch(PATCH) as mock_repo:
            mock_repo.get_link = AsyncMock(return_value=_mock_link())
            mock_repo.deactivate_link = AsyncMock(return_value=True)

            result = await service.unlink_child(db, uuid4(), uuid4())

        assert result is True
        db.commit.assert_awaited_once()

    async def test_does_not_delete_student_account(self, service, db):
        """Unlink soft-deactivates the link only — no student data is deleted."""
        with patch(PATCH) as mock_repo:
            mock_repo.get_link = AsyncMock(return_value=_mock_link())
            mock_repo.deactivate_link = AsyncMock(return_value=True)

            await service.unlink_child(db, uuid4(), uuid4())

        # Deactivate was called, but no delete method exists or was called
        mock_repo.deactivate_link.assert_awaited_once()
        # Confirm no method named "delete" was called on the repo mock
        assert not any(
            "delete" in str(call) for call in mock_repo.method_calls
        )


# ── get_child_attempts_paged ───────────────────────────────────────────────────

class TestGetChildAttemptsPaged:
    async def test_raises_forbidden_if_not_linked(self, service, db):
        with patch(PATCH) as mock_repo:
            mock_repo.get_link = AsyncMock(return_value=None)

            with pytest.raises(Forbidden):
                await service.get_child_attempts_paged(db, uuid4(), uuid4())

    async def test_returns_correct_page_slice(self, service, db):
        """Page 2 of size 2 from 5 total rows returns rows 3-4."""
        parent_id = uuid4()
        student_id = uuid4()

        # 5 simple mapping rows
        rows = [
            {"attempt_id": uuid4(), "exam_title_en": f"Exam {i}",
             "exam_title_mr": None, "paper_code": "501", "attempt_number": 1,
             "status": "submitted", "submitted_at": None, "total_score": 90,
             "total_marks": 150, "percentage": 60.0, "grade": "Average",
             "duration_seconds": 3600}
            for i in range(5)
        ]

        with patch(PATCH) as mock_repo:
            mock_repo.get_link = AsyncMock(return_value=_mock_link())
            mock_repo.get_child_attempts = AsyncMock(return_value=rows)

            result = await service.get_child_attempts_paged(
                db, parent_id, student_id, page=2, size=2
            )

        assert result["total"] == 5
        assert result["page"] == 2
        assert result["size"] == 2
        assert result["pages"] == 3
        assert len(result["items"]) == 2
