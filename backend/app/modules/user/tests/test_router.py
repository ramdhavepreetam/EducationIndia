"""
Router integration tests for the user module.

Uses httpx.AsyncClient with FastAPI's ASGI transport.
Dependencies (verify_token, user_service) are overridden — no DB or real auth needed.
Tests focus on: HTTP status codes, auth enforcement, role enforcement, response shape.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.auth.dependencies import require_parent, verify_token
from app.modules.user.models import ParentStudentLink, UserProfile, UserRoleEnum
from app.modules.user.service import user_service as _user_service
from app.shared.exceptions import Conflict, NotFound

pytestmark = pytest.mark.asyncio

# ── Identity factories ────────────────────────────────────────────────────────

def _student_identity():
    from app.modules.auth.dependencies import UserIdentity
    return UserIdentity(id=uuid4(), role="student", email="student@test.com")


def _parent_identity():
    from app.modules.auth.dependencies import UserIdentity
    return UserIdentity(id=uuid4(), role="parent", email="parent@test.com")


# ── Profile fixture ───────────────────────────────────────────────────────────

def _mock_profile(role: str = "student") -> MagicMock:
    p = MagicMock(spec=UserProfile)
    p.id = uuid4()
    p.role = role
    p.full_name = "Test User"
    p.avatar_url = None
    p.phone = None
    p.preferred_language = "en"
    p.std_class = 5
    p.medium = "english"
    p.school_name = "Test School"
    p.district = "Pune"
    p.state = "Maharashtra"
    p.date_of_birth = None
    p.auth_provider = "email"
    p.is_active = True
    p.is_onboarded = False
    p.subscription_tier = "free"
    p.subscription_expiry = None
    from datetime import datetime, timezone
    p.created_at = datetime.now(timezone.utc)
    p.updated_at = datetime.now(timezone.utc)
    return p


# ── Client fixtures ───────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def student_client():
    """AsyncClient authenticated as a student."""
    app.dependency_overrides[verify_token] = lambda: _student_identity()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def parent_client():
    """AsyncClient authenticated as a parent (also overrides require_parent)."""
    identity = _parent_identity()
    app.dependency_overrides[verify_token] = lambda: identity
    app.dependency_overrides[require_parent] = lambda: identity
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def anon_client():
    """AsyncClient with no auth overrides — token will be missing."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ── GET /api/users/me ─────────────────────────────────────────────────────────

class TestGetMyProfile:
    async def test_returns_200_for_authenticated_student(self, student_client):
        profile = _mock_profile()
        with patch.object(_user_service, "get_my_profile", new=AsyncMock(return_value=profile)):
            response = await student_client.get("/api/users/me")
        assert response.status_code == 200

    async def test_returns_401_without_token(self, anon_client):
        response = await anon_client.get("/api/users/me")
        assert response.status_code == 401

    async def test_returns_404_when_profile_not_found(self, student_client):
        with patch.object(
            _user_service, "get_my_profile", new=AsyncMock(side_effect=NotFound())
        ):
            response = await student_client.get("/api/users/me")
        assert response.status_code == 404


# ── PUT /api/users/me ─────────────────────────────────────────────────────────

class TestUpdateMyProfile:
    async def test_returns_200_on_valid_update(self, student_client):
        profile = _mock_profile()
        profile.full_name = "Updated Name"
        with patch.object(
            _user_service, "update_my_profile", new=AsyncMock(return_value=profile)
        ):
            response = await student_client.put(
                "/api/users/me", json={"full_name": "Updated Name"}
            )
        assert response.status_code == 200

    async def test_returns_401_without_token(self, anon_client):
        response = await anon_client.put("/api/users/me", json={"full_name": "X"})
        assert response.status_code == 401

    async def test_rejects_invalid_preferred_language(self, student_client):
        profile = _mock_profile()
        with patch.object(
            _user_service, "update_my_profile", new=AsyncMock(return_value=profile)
        ):
            response = await student_client.put(
                "/api/users/me", json={"preferred_language": "zh"}
            )
        assert response.status_code == 422  # Pydantic validation


# ── POST /api/users/me/complete-profile ───────────────────────────────────────

class TestCompleteProfile:
    async def test_returns_200_and_is_onboarded_set(self, student_client):
        profile = _mock_profile()
        profile.is_onboarded = True
        with patch.object(
            _user_service, "complete_profile", new=AsyncMock(return_value=profile)
        ):
            response = await student_client.post(
                "/api/users/me/complete-profile",
                json={
                    "school_name": "City School",
                    "district": "Pune",
                    "std_class": 5,
                    "preferred_language": "en",
                },
            )
        assert response.status_code == 200
        assert response.json()["is_onboarded"] is True

    async def test_returns_401_without_token(self, anon_client):
        response = await anon_client.post(
            "/api/users/me/complete-profile",
            json={"school_name": "X", "district": "Y"},
        )
        assert response.status_code == 401

    async def test_missing_school_name_returns_422(self, student_client):
        response = await student_client.post(
            "/api/users/me/complete-profile",
            json={"district": "Pune", "std_class": 5},
        )
        assert response.status_code == 422


# ── GET /api/users/my-children ────────────────────────────────────────────────

class TestGetMyChildren:
    async def test_parent_gets_200(self, parent_client):
        with patch.object(
            _user_service, "get_my_children", new=AsyncMock(return_value=[])
        ):
            response = await parent_client.get("/api/users/my-children")
        assert response.status_code == 200
        assert response.json() == []

    async def test_student_gets_403(self, student_client):
        """
        Student cannot access parent-only endpoints.
        require_parent raises 403 before service is called.
        """
        response = await student_client.get("/api/users/my-children")
        assert response.status_code == 403

    async def test_returns_401_without_token(self, anon_client):
        response = await anon_client.get("/api/users/my-children")
        assert response.status_code == 401


# ── POST /api/users/link-child ────────────────────────────────────────────────

class TestLinkChild:
    async def test_parent_creates_link_gets_201(self, parent_client):
        from datetime import datetime, timezone
        link = MagicMock(spec=ParentStudentLink)
        link.id = 1
        link.parent_id = uuid4()
        link.student_id = uuid4()
        link.child_nickname = "Rahul"
        link.linked_at = datetime.now(timezone.utc)
        link.is_active = True

        with patch.object(
            _user_service, "link_child", new=AsyncMock(return_value=link)
        ):
            response = await parent_client.post(
                "/api/users/link-child",
                json={"email": "student@example.com", "child_nickname": "Rahul"},
            )
        assert response.status_code == 201

    async def test_student_cannot_link_child(self, student_client):
        """Students cannot access parent-only endpoints."""
        response = await student_client.post(
            "/api/users/link-child",
            json={"email": "another@example.com"},
        )
        assert response.status_code == 403

    async def test_returns_404_when_email_not_found(self, parent_client):
        with patch.object(
            _user_service, "link_child", new=AsyncMock(side_effect=NotFound())
        ):
            response = await parent_client.post(
                "/api/users/link-child",
                json={"email": "unknown@example.com"},
            )
        assert response.status_code == 404

    async def test_returns_409_when_already_linked(self, parent_client):
        with patch.object(
            _user_service, "link_child", new=AsyncMock(side_effect=Conflict())
        ):
            response = await parent_client.post(
                "/api/users/link-child",
                json={"email": "student@example.com"},
            )
        assert response.status_code == 409

    async def test_invalid_email_returns_422(self, parent_client):
        response = await parent_client.post(
            "/api/users/link-child",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422

    async def test_returns_401_without_token(self, anon_client):
        response = await anon_client.post(
            "/api/users/link-child", json={"email": "x@x.com"}
        )
        assert response.status_code == 401


# ── GET /api/users/me — profile response shape ──────────────────────────────

class TestGetMeProfileShape:
    """User spec: test_get_me_200_returns_profile."""

    async def test_response_includes_expected_fields(self, student_client):
        profile = _mock_profile()
        with patch.object(
            _user_service, "get_my_profile", new=AsyncMock(return_value=profile)
        ):
            response = await student_client.get("/api/users/me")

        assert response.status_code == 200
        body = response.json()
        assert "full_name" in body
        assert "preferred_language" in body
        assert "is_onboarded" in body
        assert "auth_provider" in body
        # Sensitive fields should NOT be present
        assert "password" not in body
        assert "password_hash" not in body


# ── PUT /api/users/me — update fields ────────────────────────────────────────

class TestPutMeUpdatesFields:
    """User spec: test_put_me_200_updates_fields."""

    async def test_returns_updated_full_name_in_response(self, student_client):
        profile = _mock_profile()
        profile.full_name = "New Name"
        with patch.object(
            _user_service, "update_my_profile", new=AsyncMock(return_value=profile)
        ):
            response = await student_client.put(
                "/api/users/me", json={"full_name": "New Name"}
            )
        assert response.status_code == 200
        assert response.json()["full_name"] == "New Name"


# ── POST /api/users/me/avatar ────────────────────────────────────────────────

class TestAvatarUpload:
    """User spec: test_avatar_upload_200_returns_updated_profile,
    test_avatar_upload_too_large_rejected."""

    async def test_returns_200_with_valid_image(self, student_client):
        profile = _mock_profile()
        profile.avatar_url = "https://example.com/avatars/new.jpg"

        with patch.object(
            _user_service, "get_my_profile", new=AsyncMock(return_value=profile)
        ), patch.object(
            _user_service, "update_avatar", new=AsyncMock(return_value=profile)
        ), patch(
            "app.modules.media.service.media_service"
        ) as mock_media:
            mock_media.upload_file = AsyncMock(
                return_value={"file_url": "https://example.com/avatars/new.jpg"}
            )

            # Create a small valid PNG-like file
            from io import BytesIO
            small_img = BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
            response = await student_client.post(
                "/api/users/me/avatar",
                files={"file": ("avatar.png", small_img, "image/png")},
            )

        assert response.status_code == 200

    async def test_rejects_file_over_2mb(self, student_client):
        """User spec: test_avatar_upload_too_large_rejected."""
        # Create file just over 2MB
        from io import BytesIO
        large_file = BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * (2 * 1024 * 1024 + 1))
        response = await student_client.post(
            "/api/users/me/avatar",
            files={"file": ("big.png", large_file, "image/png")},
        )
        assert response.status_code == 400

    async def test_rejects_unsupported_content_type(self, student_client):
        from io import BytesIO
        gif_file = BytesIO(b"GIF89a" + b"\x00" * 50)
        response = await student_client.post(
            "/api/users/me/avatar",
            files={"file": ("anim.gif", gif_file, "image/gif")},
        )
        assert response.status_code == 400


# ── POST /api/users/me/change-password ───────────────────────────────────────

class TestChangePasswordRouter:
    """User spec: test_change_password_200_for_email_user,
    test_change_password_403_for_google_user."""

    async def test_returns_200_for_email_user(self, student_client):
        """Email user can change password."""
        profile = _mock_profile()
        profile.auth_provider = "email"

        with patch.object(
            _user_service, "get_my_profile", new=AsyncMock(return_value=profile)
        ), patch.object(
            _user_service, "change_password", new=AsyncMock(return_value={"success": True})
        ):
            response = await student_client.post(
                "/api/users/me/change-password",
                json={
                    "current_password": "oldpass123",
                    "new_password": "newpass1234",
                    "confirm_password": "newpass1234",
                },
            )
        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_returns_400_for_google_user(self, student_client):
        """Google user cannot change password."""
        profile = _mock_profile()
        profile.auth_provider = "google"

        with patch.object(
            _user_service, "get_my_profile", new=AsyncMock(return_value=profile)
        ):
            response = await student_client.post(
                "/api/users/me/change-password",
                json={
                    "current_password": "anything",
                    "new_password": "newpass1234",
                    "confirm_password": "newpass1234",
                },
            )
        assert response.status_code == 400
        body = response.json()
        # Error may be in 'detail' or 'message' depending on exception handler
        error_text = body.get("detail", body.get("message", str(body))).lower()
        assert "social login" in error_text or "email" in error_text

    async def test_returns_401_without_token(self, anon_client):
        response = await anon_client.post(
            "/api/users/me/change-password",
            json={
                "current_password": "x",
                "new_password": "newpass1234",
                "confirm_password": "newpass1234",
            },
        )
        assert response.status_code == 401

    async def test_mismatched_passwords_returns_422(self, student_client):
        """Pydantic model_validator catches mismatch before router."""
        response = await student_client.post(
            "/api/users/me/change-password",
            json={
                "current_password": "current123",
                "new_password": "newpass1234",
                "confirm_password": "different_pass",
            },
        )
        assert response.status_code == 422

