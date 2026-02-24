"""
Security boundary tests for the parent module.

These tests verify auth enforcement at the router level:
  - Role enforcement: students cannot access parent endpoints (real require_parent fires)
  - Token enforcement: missing token returns 401
  - Cross-parent isolation: parent cannot see another parent's child (service raises Forbidden)
  - Self-link prevention: parent cannot link to own account (service raises BadRequest)
  - Link deactivation: after unlink, get_child_detail returns 403

Only verify_token is overridden in role tests — require_parent is NOT overridden
so the real role check fires. Service is mocked for data-level boundary tests.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.auth.dependencies import UserIdentity, require_parent, verify_token
from app.modules.user.parent_schemas import ChildProfileSchema
from app.modules.user.parent_service import parent_service as _parent_service
from app.shared.exceptions import BadRequest, Forbidden, NotFound

pytestmark = pytest.mark.asyncio

_STUDENT_ID = uuid4()


# ── Identity helpers ───────────────────────────────────────────────────────────

def _identity(role: str, user_id=None) -> UserIdentity:
    return UserIdentity(id=user_id or uuid4(), role=role, email=f"{role}@test.com")


def _child_profile(student_id=None) -> ChildProfileSchema:
    return ChildProfileSchema(
        student_id=student_id or _STUDENT_ID,
        full_name="Arjun S",
        std_class=5,
        medium=None,
        school_name="City School",
        district="Pune",
        avatar_url=None,
        child_nickname=None,
        is_onboarded=True,
        linked_at=datetime.now(timezone.utc),
    )


# ── Client fixtures ────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def student_client():
    """Student token — require_parent NOT overridden (real role check fires)."""
    identity = _identity("student")
    app.dependency_overrides[verify_token] = lambda: identity
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def anon_client():
    """No token at all."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@asynccontextmanager
async def _parent_client_context(parent_id=None):
    """Async context manager: parent-authenticated client with automatic cleanup."""
    identity = _identity("parent", parent_id)
    app.dependency_overrides[verify_token] = lambda: identity
    app.dependency_overrides[require_parent] = lambda: identity
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


# ── Role enforcement ───────────────────────────────────────────────────────────

class TestStudentBlockedFromAllParentEndpoints:
    """Student role must receive 403 on every parent endpoint (not 422, not 500)."""

    async def test_dashboard_blocked(self, student_client):
        response = await student_client.get("/api/parent/dashboard")
        assert response.status_code == 403

    async def test_children_list_blocked(self, student_client):
        response = await student_client.get("/api/parent/children")
        assert response.status_code == 403

    async def test_link_child_blocked(self, student_client):
        response = await student_client.post(
            "/api/parent/children/link",
            json={"student_email": "x@test.com"},
        )
        assert response.status_code == 403

    async def test_child_detail_blocked(self, student_client):
        response = await student_client.get(
            f"/api/parent/children/{_STUDENT_ID}"
        )
        assert response.status_code == 403

    async def test_child_attempts_blocked(self, student_client):
        response = await student_client.get(
            f"/api/parent/children/{_STUDENT_ID}/attempts"
        )
        assert response.status_code == 403

    async def test_update_nickname_blocked(self, student_client):
        response = await student_client.put(
            f"/api/parent/children/{_STUDENT_ID}/nickname",
            json={"child_nickname": "Buddy"},
        )
        assert response.status_code == 403

    async def test_unlink_blocked(self, student_client):
        response = await student_client.delete(
            f"/api/parent/children/{_STUDENT_ID}/unlink"
        )
        assert response.status_code == 403


# ── Token enforcement ──────────────────────────────────────────────────────────

class TestUnauthenticatedReturns401:
    async def test_dashboard_requires_token(self, anon_client):
        response = await anon_client.get("/api/parent/dashboard")
        assert response.status_code == 401

    async def test_children_list_requires_token(self, anon_client):
        response = await anon_client.get("/api/parent/children")
        assert response.status_code == 401

    async def test_link_child_requires_token(self, anon_client):
        response = await anon_client.post(
            "/api/parent/children/link",
            json={"student_email": "x@test.com"},
        )
        assert response.status_code == 401

    async def test_child_detail_requires_token(self, anon_client):
        response = await anon_client.get(
            f"/api/parent/children/{_STUDENT_ID}"
        )
        assert response.status_code == 401


# ── Cross-parent isolation ─────────────────────────────────────────────────────

class TestParentCannotSeeOtherParentChildren:
    async def test_parent_without_link_gets_403(self):
        """
        Parent B requests child detail for a student linked to parent A.
        Service raises Forbidden → router returns 403.
        """
        async with _parent_client_context() as client:
            with patch.object(
                _parent_service,
                "get_child_detail",
                new=AsyncMock(side_effect=Forbidden("Not linked to this student")),
            ):
                response = await client.get(
                    f"/api/parent/children/{_STUDENT_ID}"
                )
        assert response.status_code == 403

    async def test_parent_without_link_cannot_see_attempts(self):
        async with _parent_client_context() as client:
            with patch.object(
                _parent_service,
                "get_child_attempts_paged",
                new=AsyncMock(side_effect=Forbidden("Not linked to this student")),
            ):
                response = await client.get(
                    f"/api/parent/children/{_STUDENT_ID}/attempts"
                )
        assert response.status_code == 403

    async def test_parent_without_link_cannot_see_topics(self):
        async with _parent_client_context() as client:
            with patch.object(
                _parent_service,
                "get_child_topics",
                new=AsyncMock(side_effect=Forbidden("Not linked to this student")),
            ):
                response = await client.get(
                    f"/api/parent/children/{_STUDENT_ID}/topics"
                )
        assert response.status_code == 403


# ── Self-link prevention ───────────────────────────────────────────────────────

class TestParentCannotLinkToSelf:
    async def test_self_link_returns_400(self):
        """Service raises BadRequest when parent tries to link their own email."""
        async with _parent_client_context() as client:
            with patch.object(
                _parent_service,
                "link_child",
                new=AsyncMock(
                    side_effect=BadRequest("You cannot link to your own account")
                ),
            ):
                response = await client.post(
                    "/api/parent/children/link",
                    json={"student_email": "parent@test.com"},
                )
        assert response.status_code == 400


# ── Non-student accounts ───────────────────────────────────────────────────────

class TestCannotLinkNonStudentEmail:
    async def test_admin_email_returns_404(self):
        """Admin or parent email passed to link_child → service raises NotFound."""
        async with _parent_client_context() as client:
            with patch.object(
                _parent_service,
                "link_child",
                new=AsyncMock(
                    side_effect=NotFound("No student account found with this email")
                ),
            ):
                response = await client.post(
                    "/api/parent/children/link",
                    json={"student_email": "admin@test.com"},
                )
        assert response.status_code == 404


# ── Deactivated link blocks access ────────────────────────────────────────────

class TestDeactivatedLinkBlocksAccess:
    async def test_unlinked_child_returns_403_on_get_detail(self):
        """
        After a parent unlinks a child, get_child_detail must return 403.
        Simulated by: service.unlink_child succeeds, then get_child_detail raises Forbidden.
        """
        async with _parent_client_context() as client:
            # Step 1: unlink succeeds
            with patch.object(
                _parent_service, "unlink_child", new=AsyncMock(return_value=True)
            ):
                unlink_response = await client.delete(
                    f"/api/parent/children/{_STUDENT_ID}/unlink"
                )
            assert unlink_response.status_code == 200

            # Step 2: subsequent get returns 403 (link now inactive)
            with patch.object(
                _parent_service,
                "get_child_detail",
                new=AsyncMock(side_effect=Forbidden("Not linked to this student")),
            ):
                detail_response = await client.get(
                    f"/api/parent/children/{_STUDENT_ID}"
                )
            assert detail_response.status_code == 403
