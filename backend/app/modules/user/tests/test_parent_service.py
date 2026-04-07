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

from app.modules.user.models import ChildProfile
from app.modules.user.parent_service import ParentService
from app.shared.exceptions import Forbidden, NotFound

pytestmark = pytest.mark.asyncio


# ── Factories ──────────────────────────────────────────────────────────────────

def _mock_profile(parent_id=None, child_id=None) -> MagicMock:
    """A MagicMock shaped like a ChildProfile ORM object."""
    p = MagicMock(spec=ChildProfile)
    p.id = child_id or uuid4()
    p.parent_id = parent_id or uuid4()
    p.name = "Arjun S"
    p.std_class = 5
    p.medium = "english"
    p.school_name = "City School"
    p.district = "Pune"
    p.avatar_color = "#3B82F6"
    p.is_active = True
    return p





def _default_stats() -> dict:
    return {
        "total_attempts": 0,
        "avg_percentage": None,
        "best_score": None,
        "best_percentage": None,
        "last_active": None,
        "exams_completed": 0,
    }





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
        with patch("app.modules.user.parent_service.ChildRepository.get_children", new_callable=AsyncMock) as mock_get_children:
            mock_get_children.return_value = []
            result = await service.get_dashboard(db, parent_id)

        assert result.children == []
        assert result.selected_child_detail is None

    async def test_loads_first_child_detail_when_children_exist(self, service, db):
        """When children exist, dashboard includes first child's detail."""
        parent_id = uuid4()
        child_id = uuid4()
        child_profile = _mock_profile(parent_id, child_id)

        with patch("app.modules.user.parent_service.ChildRepository.get_children", new_callable=AsyncMock) as mock_get_children, \
             patch("app.modules.user.parent_service.ChildRepository.get_by_id", new_callable=AsyncMock) as mock_get_by_id, \
             patch(PATCH + ".get_child_stats", new_callable=AsyncMock) as mock_stats, \
             patch(PATCH + ".get_child_attempts", new_callable=AsyncMock) as mock_attempts, \
             patch(PATCH + ".get_child_topic_performance", new_callable=AsyncMock) as mock_topics:
            
            mock_get_children.return_value = [child_profile]
            mock_get_by_id.return_value = child_profile
            mock_stats.return_value = _default_stats()
            mock_attempts.return_value = []
            mock_topics.return_value = []

            result = await service.get_dashboard(db, parent_id)

        assert len(result.children) == 1
        assert result.selected_child_detail is not None
        assert result.children[0].id == child_id


# ── get_child_detail ───────────────────────────────────────────────────────────

class TestGetChildDetail:
    async def test_raises_forbidden_if_not_linked(self, service, db):
        """Service rejects access when no active link exists."""
        with patch("app.modules.user.parent_service.ChildRepository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
            mock_get_by_id.return_value = None

            with pytest.raises(Forbidden):
                await service.get_child_detail(db, uuid4(), uuid4())

    async def test_returns_full_detail_when_linked(self, service, db):
        parent_id = uuid4()
        child_id = uuid4()
        child_profile = _mock_profile(parent_id, child_id)

        with patch("app.modules.user.parent_service.ChildRepository.get_by_id", new_callable=AsyncMock) as mock_get_by_id, \
             patch(PATCH + ".get_child_stats", new_callable=AsyncMock) as mock_stats, \
             patch(PATCH + ".get_child_attempts", new_callable=AsyncMock) as mock_attempts, \
             patch(PATCH + ".get_child_topic_performance", new_callable=AsyncMock) as mock_topics:
            
            mock_get_by_id.return_value = child_profile
            mock_stats.return_value = _default_stats()
            mock_attempts.return_value = []
            mock_topics.return_value = []

            result = await service.get_child_detail(db, parent_id, child_id)

        assert result.profile.id == child_id
        assert result.stats.total_attempts == 0

    async def test_weak_topics_split_correctly(self, service, db):
        """Topics with status=weak go to weak_topics, strong → strong_topics, average ignored."""
        parent_id = uuid4()
        child_id = uuid4()
        child_profile = _mock_profile(parent_id, child_id)

        topics = [
            {"topic_id": 1, "topic_name_en": "Fractions", "topic_name_mr": None,
             "avg_percentage": 42.0, "attempts_count": 3, "status": "weak"},
            {"topic_id": 2, "topic_name_en": "Grammar",   "topic_name_mr": None,
             "avg_percentage": 88.0, "attempts_count": 5, "status": "strong"},
            {"topic_id": 3, "topic_name_en": "Maps",      "topic_name_mr": None,
             "avg_percentage": 60.0, "attempts_count": 2, "status": "average"},
        ]

        with patch("app.modules.user.parent_service.ChildRepository.get_by_id", new_callable=AsyncMock) as mock_get_by_id, \
             patch(PATCH + ".get_child_stats", new_callable=AsyncMock) as mock_stats, \
             patch(PATCH + ".get_child_attempts", new_callable=AsyncMock) as mock_attempts, \
             patch(PATCH + ".get_child_topic_performance", new_callable=AsyncMock) as mock_topics:
            
            mock_get_by_id.return_value = child_profile
            mock_stats.return_value = _default_stats()
            mock_attempts.return_value = []
            mock_topics.return_value = topics

            result = await service.get_child_detail(db, parent_id, child_id)

        assert len(result.weak_topics) == 1
        assert result.weak_topics[0].topic_name_en == "Fractions"
        assert len(result.strong_topics) == 1
        # Average topics not included in either list
        assert all(t.status != "average" for t in result.weak_topics)
        assert all(t.status != "average" for t in result.strong_topics)

    async def test_strong_topics_sorted_descending(self, service, db):
        """Strong topics sorted by avg_percentage DESC (best first)."""
        parent_id = uuid4()
        child_id = uuid4()
        child_profile = _mock_profile(parent_id, child_id)

        topics = [
            {"topic_id": 1, "topic_name_en": "A", "topic_name_mr": None,
             "avg_percentage": 72.0, "attempts_count": 3, "status": "strong"},
            {"topic_id": 2, "topic_name_en": "B", "topic_name_mr": None,
             "avg_percentage": 95.0, "attempts_count": 5, "status": "strong"},
        ]

        with patch("app.modules.user.parent_service.ChildRepository.get_by_id", new_callable=AsyncMock) as mock_get_by_id, \
             patch(PATCH + ".get_child_stats", new_callable=AsyncMock) as mock_stats, \
             patch(PATCH + ".get_child_attempts", new_callable=AsyncMock) as mock_attempts, \
             patch(PATCH + ".get_child_topic_performance", new_callable=AsyncMock) as mock_topics:
            
            mock_get_by_id.return_value = child_profile
            mock_stats.return_value = _default_stats()
            mock_attempts.return_value = []
            mock_topics.return_value = topics

            result = await service.get_child_detail(db, parent_id, child_id)

        assert result.strong_topics[0].avg_percentage == 95.0
        assert result.strong_topics[1].avg_percentage == 72.0



# ── get_child_attempts_paged ───────────────────────────────────────────────────

class TestGetChildAttemptsPaged:
    async def test_raises_forbidden_if_not_linked(self, service, db):
        with patch("app.modules.user.parent_service.ChildRepository.get_by_id", new_callable=AsyncMock) as mock_get_by_id:
            mock_get_by_id.return_value = None

            with pytest.raises(Forbidden):
                await service.get_child_attempts_paged(db, uuid4(), uuid4())

    async def test_returns_correct_page_slice(self, service, db):
        """Page 2 of size 2 from 5 total rows returns rows 3-4."""
        parent_id = uuid4()
        child_id = uuid4()
        child_profile = _mock_profile(parent_id, child_id)

        # 5 simple mapping rows
        rows = [
            {"attempt_id": uuid4(), "exam_title_en": f"Exam {i}",
             "exam_title_mr": None, "paper_code": "501", "attempt_number": 1,
             "status": "submitted", "submitted_at": None, "total_score": 90,
             "total_marks": 150, "percentage": 60.0, "grade": "Average",
             "duration_seconds": 3600}
            for i in range(5)
        ]

        with patch("app.modules.user.parent_service.ChildRepository.get_by_id", new_callable=AsyncMock) as mock_get_by_id, \
             patch(PATCH + ".get_child_attempts", new_callable=AsyncMock) as mock_attempts:
            
            mock_get_by_id.return_value = child_profile
            mock_attempts.return_value = rows

            result = await service.get_child_attempts_paged(
                db, parent_id, child_id, page=2, size=2
            )

        assert result["total"] == 5
        assert result["page"] == 2
        assert result["size"] == 2
        assert result["pages"] == 3
        assert len(result["items"]) == 2
