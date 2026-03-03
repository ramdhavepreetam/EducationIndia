"""
Unit tests for ChildService.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.user.child_schemas import CreateChildRequest, UpdateChildRequest
from app.modules.user.child_service import ChildService
from app.modules.user.models import ChildProfile
from app.shared.exceptions import BadRequest, Forbidden, NotFound
from datetime import datetime, timezone

pytestmark = pytest.mark.asyncio


def _mock_child_profile(parent_id, child_id=None):
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


@pytest.fixture
def service():
    return ChildService()


@pytest.fixture
def db():
    db = AsyncMock()
    db.commit = AsyncMock()
    return db



class TestChildService:

    async def test_get_children_empty(self, service, db):
        with patch.object(service.repo, 'get_children', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []

            res = await service.get_children(uuid4(), db)
            assert res == []

    async def test_get_children_success(self, service, db):
        parent_id = uuid4()
        child1 = _mock_child_profile(parent_id)
        with patch.object(service.repo, 'get_children', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [child1]

            res = await service.get_children(parent_id, db)
            assert len(res) == 1

    async def test_create_child_success(self, service, db):
        parent_id = uuid4()
        req = CreateChildRequest(name="New Child", std_class=5)
        new_child = _mock_child_profile(parent_id)

        with patch.object(service.repo, 'get_children', new_callable=AsyncMock) as mock_get, \
             patch.object(service.repo, 'create', new_callable=AsyncMock) as mock_create:
            mock_get.return_value = [new_child] # or empty array depending
            mock_get.return_value = [] # existing children length 0
            mock_create.return_value = new_child

            res = await service.create_child(parent_id, req, db)
            assert res.id == new_child.id

    async def test_create_child_limit_reached(self, service, db):
        parent_id = uuid4()
        req = CreateChildRequest(name="Tenth Child", std_class=5)

        with patch.object(service.repo, 'get_children', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = [AsyncMock()] * 10

            with pytest.raises(BadRequest, match="Maximum 10 child"):
                await service.create_child(parent_id, req, db)

    async def test_update_child_not_found_or_forbidden(self, service, db):
        parent_id = uuid4()
        child_id = uuid4()
        req = UpdateChildRequest(name="Renamed")

        with patch.object(service.repo, 'get_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            with pytest.raises(NotFound, match="not found"):
                await service.update_child(child_id, parent_id, req, db)

    async def test_update_child_success(self, service, db):
        parent_id = uuid4()
        child_id = uuid4()
        req = UpdateChildRequest(name="Renamed")
        updated_child = _mock_child_profile(parent_id, child_id)

        with patch.object(service.repo, 'get_by_id', new_callable=AsyncMock) as mock_get, \
             patch.object(service.repo, 'update', new_callable=AsyncMock) as mock_update:
            mock_get.return_value = updated_child
            mock_update.return_value = updated_child

            res = await service.update_child(child_id, parent_id, req, db)
            assert res.id == updated_child.id

    async def test_delete_child_not_found(self, service, db):
        parent_id = uuid4()
        child_id = uuid4()

        with patch.object(service.repo, 'get_by_id', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            with pytest.raises(NotFound):
                await service.delete_child(child_id, parent_id, db)

    async def test_delete_child_success(self, service, db):
        parent_id = uuid4()
        child_id = uuid4()
        child = _mock_child_profile(parent_id, child_id)

        with patch.object(service.repo, 'get_by_id', new_callable=AsyncMock) as mock_get, \
             patch.object(service.repo, 'deactivate', new_callable=AsyncMock) as mock_deactivate:
            mock_get.return_value = child
            mock_deactivate.return_value = True

            res = await service.delete_child(child_id, parent_id, db)
            assert res is True
