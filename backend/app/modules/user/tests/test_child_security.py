"""
Security-focused tests for Child Profiles (ADR-013).

Covers:
  - Ownership validation (parent A cannot access parent B's children)
  - Max children limit
  - Start exam rejected/accepted based on child ownership
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.child_repository import ChildRepository
from app.modules.user.child_service import ChildService
from app.modules.user.child_schemas import CreateChildRequest
from app.modules.user.models import ChildProfile
from app.shared.exceptions import BadRequest, Forbidden
from datetime import datetime, timezone

pytestmark = pytest.mark.asyncio


def _mock_child(parent_id, child_id=None):
    c = MagicMock(spec=ChildProfile)
    c.id = child_id or uuid4()
    c.parent_id = parent_id
    c.name = "Test Child"
    c.std_class = 5
    c.medium = "english"
    c.school_name = None
    c.district = None
    c.avatar_color = "#3B82F6"
    c.is_active = True
    c.created_at = datetime.now(timezone.utc)
    return c


class TestChildSecurity:

    @pytest.fixture
    def repo(self):
        return ChildRepository()

    @pytest.fixture
    def service(self):
        return ChildService()

    @pytest.fixture
    def db(self):
        return AsyncMock(spec=AsyncSession)

    # ── Ownership validation ──────────────────────────────────────────────

    async def test_validate_ownership_success(self, repo, db, monkeypatch):
        """Parent can access their own child profile."""
        parent_id = uuid4()
        child_id = uuid4()

        async def mock_get_by_id(*args, **kwargs):
            return ChildProfile(id=child_id, parent_id=parent_id)

        monkeypatch.setattr(repo, "get_by_id", mock_get_by_id)

        is_owner = await repo.validate_ownership(child_id, parent_id, db)
        assert is_owner is True

    async def test_validate_ownership_failure(self, repo, db, monkeypatch):
        """Parent A cannot validate ownership of parent B's child."""
        parent_a = uuid4()
        child_of_b = uuid4()

        async def mock_get_by_id(*args, **kwargs):
            return None  # get_by_id filters by parent_id, so returns None

        monkeypatch.setattr(repo, "get_by_id", mock_get_by_id)

        is_owner = await repo.validate_ownership(child_of_b, parent_a, db)
        assert is_owner is False

    async def test_parent_A_cannot_access_parent_B_children(self, service, db):
        """get_child() raises NotFound when parent tries to access another parent's child."""
        from app.shared.exceptions import NotFound

        parent_a = uuid4()
        child_of_b = uuid4()

        with patch.object(service.repo, 'get_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None  # Ownership check fails

            with pytest.raises(NotFound, match="not found"):
                await service.get_child(child_of_b, parent_a, db)

    async def test_parent_cannot_create_more_than_2_children(self, service, db):
        """Service enforces max 2 child profiles per parent."""
        parent_id = uuid4()
        req = CreateChildRequest(name="Third Child", std_class=5)

        with patch.object(service.repo, 'get_children', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [_mock_child(parent_id) for _ in range(2)]

            with pytest.raises(BadRequest, match="Maximum 2 child"):
                await service.create_child(parent_id, req, db)

    # ── Attempt start with child_profile_id ───────────────────────────────

    async def test_start_exam_rejected_for_unowned_child(self):
        """start_exam() raises Forbidden when child doesn't belong to parent."""
        from app.modules.attempt.service import AttemptService
        from app.modules.attempt.schemas import StartAttemptRequest

        attempt_svc = AttemptService()
        parent_id = uuid4()
        unowned_child_id = uuid4()

        request = StartAttemptRequest(
            exam_id=1,
            child_profile_id=unowned_child_id,
        )

        db = AsyncMock(spec=AsyncSession)

        # Mock catalog to return a valid exam
        mock_exam = MagicMock()
        mock_exam.duration_minutes = 90

        with patch('app.modules.attempt.service.catalog_service') as mock_catalog, \
             patch('app.modules.user.child_repository.ChildRepository.validate_ownership',
                   new_callable=AsyncMock) as mock_ownership:

            mock_catalog.get_active_exam = AsyncMock(return_value=mock_exam)
            mock_ownership.return_value = False  # Not owner

            with pytest.raises(Forbidden, match="Child profile not found"):
                await attempt_svc.start_exam(db, parent_id, request)

    async def test_start_exam_succeeds_for_owned_child(self):
        """start_exam() proceeds past ownership check when child belongs to parent."""
        from app.modules.attempt.service import AttemptService
        from app.modules.attempt.schemas import StartAttemptRequest

        attempt_svc = AttemptService()
        parent_id = uuid4()
        owned_child_id = uuid4()

        request = StartAttemptRequest(
            exam_id=1,
            child_profile_id=owned_child_id,
        )

        db = AsyncMock(spec=AsyncSession)

        mock_exam = MagicMock()
        mock_exam.duration_minutes = 90

        mock_attempt = MagicMock()
        mock_attempt.id = uuid4()
        mock_attempt.exam_id = 1
        mock_attempt.attempt_number = 1
        mock_attempt.status = MagicMock(value="ongoing")
        mock_attempt.started_at = datetime.now(timezone.utc)

        with patch('app.modules.attempt.service.catalog_service') as mock_catalog, \
             patch('app.modules.user.child_repository.ChildRepository.validate_ownership',
                   new_callable=AsyncMock) as mock_ownership, \
             patch('app.modules.attempt.service.attempt_repository') as mock_repo, \
             patch('app.shared.access_control.get_access_context',
                   new_callable=AsyncMock) as mock_ctx:

            mock_catalog.get_active_exam = AsyncMock(return_value=mock_exam)
            mock_ownership.return_value = True  # Owner

            # Mock access context as paid user (ADR-014)
            from app.shared.access_control import AccessContext
            mock_ctx.return_value = AccessContext(
                parent_id=parent_id, is_paid=True, free_exam_id=1, free_max_attempts=3,
                entitled_exam_ids={1}
            )

            mock_repo.get_ongoing_attempt = AsyncMock(return_value=None)
            mock_repo.get_attempt_number = AsyncMock(return_value=1)
            mock_repo.create_attempt = AsyncMock(return_value=mock_attempt)

            result = await attempt_svc.start_exam(db, parent_id, request)
            assert result.attempt_id == mock_attempt.id
            assert result.status == "ongoing"
