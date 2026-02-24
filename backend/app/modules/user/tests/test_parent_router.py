"""
Router integration tests for the parent module.

Uses httpx.AsyncClient with FastAPI's ASGI transport.
Dependencies (verify_token, require_parent, get_db) are overridden.
Service is mocked via patch.object.
Tests focus on: HTTP status codes, auth enforcement, role enforcement, response shape.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.auth.dependencies import UserIdentity, require_parent, verify_token
from app.modules.user.parent_schemas import (
    ChildDetailSchema,
    ChildProfileSchema,
    ChildStatsSchema,
    ParentDashboardSchema,
    WeakTopicSchema,
)
from app.modules.user.parent_service import parent_service as _parent_service
from app.shared.exceptions import Conflict, Forbidden, NotFound

pytestmark = pytest.mark.asyncio

_STUDENT_ID = uuid4()


# ── Identity factories ─────────────────────────────────────────────────────────

def _parent_identity():
    return UserIdentity(id=uuid4(), role="parent", email="parent@test.com")


def _student_identity():
    return UserIdentity(id=uuid4(), role="student", email="student@test.com")


# ── Schema factories ───────────────────────────────────────────────────────────

def _child_profile_schema(student_id=None) -> ChildProfileSchema:
    return ChildProfileSchema(
        student_id=student_id or _STUDENT_ID,
        full_name="Arjun S",
        std_class=5,
        medium=None,
        school_name="City School",
        district="Pune",
        avatar_url=None,
        child_nickname="Chhotu",
        is_onboarded=True,
        linked_at=datetime.now(timezone.utc),
    )


def _child_detail_schema(student_id=None) -> ChildDetailSchema:
    return ChildDetailSchema(
        profile=_child_profile_schema(student_id),
        stats=ChildStatsSchema(
            total_attempts=0,
            avg_percentage=None,
            best_score=None,
            best_percentage=None,
            last_active=None,
            exams_completed=0,
        ),
        recent_attempts=[],
        weak_topics=[],
        strong_topics=[],
    )


def _dashboard_schema() -> ParentDashboardSchema:
    return ParentDashboardSchema(
        children=[_child_profile_schema()],
        selected_child_detail=_child_detail_schema(),
    )


# ── Client fixtures ────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def parent_client():
    """AsyncClient authenticated as a parent."""
    identity = _parent_identity()
    app.dependency_overrides[verify_token] = lambda: identity
    app.dependency_overrides[require_parent] = lambda: identity
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def student_client():
    """AsyncClient authenticated as a student (wrong role for parent endpoints)."""
    identity = _student_identity()
    app.dependency_overrides[verify_token] = lambda: identity
    # Note: require_parent is NOT overridden — real role check fires
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def anon_client():
    """AsyncClient with no auth."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ── GET /api/parent/dashboard ─────────────────────────────────────────────────

class TestGetDashboard:
    async def test_200_for_parent_role(self, parent_client):
        with patch.object(
            _parent_service, "get_dashboard",
            new=AsyncMock(return_value=_dashboard_schema())
        ):
            response = await parent_client.get("/api/parent/dashboard")
        assert response.status_code == 200
        assert "children" in response.json()

    async def test_403_for_student_role(self, student_client):
        response = await student_client.get("/api/parent/dashboard")
        assert response.status_code == 403

    async def test_401_for_no_token(self, anon_client):
        response = await anon_client.get("/api/parent/dashboard")
        assert response.status_code == 401

    async def test_empty_dashboard_returned_as_200(self, parent_client):
        """Empty children list is a valid response (not 404)."""
        empty = ParentDashboardSchema(children=[], selected_child_detail=None)
        with patch.object(
            _parent_service, "get_dashboard", new=AsyncMock(return_value=empty)
        ):
            response = await parent_client.get("/api/parent/dashboard")
        assert response.status_code == 200
        assert response.json()["children"] == []


# ── GET /api/parent/children ──────────────────────────────────────────────────

class TestGetChildren:
    async def test_200_returns_list(self, parent_client):
        with patch.object(
            _parent_service, "get_children",
            new=AsyncMock(return_value=[_child_profile_schema()])
        ):
            response = await parent_client.get("/api/parent/children")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_403_for_student_role(self, student_client):
        response = await student_client.get("/api/parent/children")
        assert response.status_code == 403

    async def test_401_for_no_token(self, anon_client):
        response = await anon_client.get("/api/parent/children")
        assert response.status_code == 401


# ── POST /api/parent/children/link ───────────────────────────────────────────

class TestLinkChild:
    async def test_201_returns_child_profile(self, parent_client):
        profile = _child_profile_schema()
        with patch.object(
            _parent_service, "link_child", new=AsyncMock(return_value=profile)
        ):
            response = await parent_client.post(
                "/api/parent/children/link",
                json={"student_email": "arjun@test.com"},
            )
        assert response.status_code == 201
        assert "student_id" in response.json()

    async def test_404_for_unknown_email(self, parent_client):
        with patch.object(
            _parent_service, "link_child",
            new=AsyncMock(side_effect=NotFound("No student account"))
        ):
            response = await parent_client.post(
                "/api/parent/children/link",
                json={"student_email": "ghost@test.com"},
            )
        assert response.status_code == 404

    async def test_409_for_already_linked(self, parent_client):
        with patch.object(
            _parent_service, "link_child",
            new=AsyncMock(side_effect=Conflict("Already monitoring"))
        ):
            response = await parent_client.post(
                "/api/parent/children/link",
                json={"student_email": "arjun@test.com"},
            )
        assert response.status_code == 409

    async def test_403_for_student_role(self, student_client):
        response = await student_client.post(
            "/api/parent/children/link",
            json={"student_email": "someone@test.com"},
        )
        assert response.status_code == 403

    async def test_401_for_no_token(self, anon_client):
        response = await anon_client.post(
            "/api/parent/children/link",
            json={"student_email": "x@x.com"},
        )
        assert response.status_code == 401


# ── GET /api/parent/children/{student_id} ─────────────────────────────────────

class TestGetChildDetail:
    async def test_200_returns_full_detail(self, parent_client):
        detail = _child_detail_schema()
        with patch.object(
            _parent_service, "get_child_detail", new=AsyncMock(return_value=detail)
        ):
            response = await parent_client.get(
                f"/api/parent/children/{_STUDENT_ID}"
            )
        assert response.status_code == 200
        assert "profile" in response.json()
        assert "stats" in response.json()

    async def test_403_for_unlinked_parent(self, parent_client):
        with patch.object(
            _parent_service, "get_child_detail",
            new=AsyncMock(side_effect=Forbidden("Not linked"))
        ):
            response = await parent_client.get(
                f"/api/parent/children/{_STUDENT_ID}"
            )
        assert response.status_code == 403

    async def test_403_for_student_role(self, student_client):
        response = await student_client.get(f"/api/parent/children/{_STUDENT_ID}")
        assert response.status_code == 403

    async def test_401_for_no_token(self, anon_client):
        response = await anon_client.get(f"/api/parent/children/{_STUDENT_ID}")
        assert response.status_code == 401


# ── PUT /api/parent/children/{student_id}/nickname ────────────────────────────

class TestUpdateNickname:
    async def test_200_returns_updated_profile(self, parent_client):
        updated = _child_profile_schema()
        with patch.object(
            _parent_service, "update_nickname", new=AsyncMock(return_value=updated)
        ):
            response = await parent_client.put(
                f"/api/parent/children/{_STUDENT_ID}/nickname",
                json={"child_nickname": "Chhotu"},
            )
        assert response.status_code == 200

    async def test_404_if_link_not_found(self, parent_client):
        with patch.object(
            _parent_service, "update_nickname",
            new=AsyncMock(side_effect=NotFound("Link not found"))
        ):
            response = await parent_client.put(
                f"/api/parent/children/{_STUDENT_ID}/nickname",
                json={"child_nickname": "Buddy"},
            )
        assert response.status_code == 404

    async def test_422_for_nickname_too_long(self, parent_client):
        """Nickname field has max_length=50 — Pydantic rejects longer values."""
        response = await parent_client.put(
            f"/api/parent/children/{_STUDENT_ID}/nickname",
            json={"child_nickname": "X" * 51},
        )
        assert response.status_code == 422


# ── DELETE /api/parent/children/{student_id}/unlink ───────────────────────────

class TestUnlinkChild:
    async def test_200_returns_success(self, parent_client):
        with patch.object(
            _parent_service, "unlink_child", new=AsyncMock(return_value=True)
        ):
            response = await parent_client.delete(
                f"/api/parent/children/{_STUDENT_ID}/unlink"
            )
        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_404_if_not_linked(self, parent_client):
        with patch.object(
            _parent_service, "unlink_child",
            new=AsyncMock(side_effect=NotFound("Link not found"))
        ):
            response = await parent_client.delete(
                f"/api/parent/children/{_STUDENT_ID}/unlink"
            )
        assert response.status_code == 404

    async def test_403_for_student_role(self, student_client):
        response = await student_client.delete(
            f"/api/parent/children/{_STUDENT_ID}/unlink"
        )
        assert response.status_code == 403

    async def test_401_for_no_token(self, anon_client):
        response = await anon_client.delete(
            f"/api/parent/children/{_STUDENT_ID}/unlink"
        )
        assert response.status_code == 401


# ── GET /api/parent/children/{student_id}/attempts ───────────────────────────

class TestGetChildAttempts:
    async def test_200_returns_paginated_dict(self, parent_client):
        payload = {"items": [], "total": 0, "page": 1, "size": 10, "pages": 0}
        with patch.object(
            _parent_service, "get_child_attempts_paged",
            new=AsyncMock(return_value=payload)
        ):
            response = await parent_client.get(
                f"/api/parent/children/{_STUDENT_ID}/attempts"
            )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 0

    async def test_403_for_unlinked_parent(self, parent_client):
        with patch.object(
            _parent_service, "get_child_attempts_paged",
            new=AsyncMock(side_effect=Forbidden("Not linked"))
        ):
            response = await parent_client.get(
                f"/api/parent/children/{_STUDENT_ID}/attempts"
            )
        assert response.status_code == 403
