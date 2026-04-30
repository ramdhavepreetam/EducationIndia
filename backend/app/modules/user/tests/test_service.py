"""
Unit tests for UserService.

All tests mock user_repository so no database is needed.
Uses unittest.mock.AsyncMock for async repository methods.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.user.models import ParentStudentLink, UserProfile, UserRoleEnum
from app.modules.user.schemas import (
    ChangePasswordRequest,
    CompleteProfileRequest,
    LinkChildRequest,
    UpdateProfileRequest,
)
from app.modules.user.service import UserService
from app.shared.exceptions import BadRequest, Conflict, NotFound

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service():
    return UserService()


@pytest.fixture
def db():
    return AsyncMock()


@pytest.fixture
def student_profile():
    profile = MagicMock(spec=UserProfile)
    profile.id = uuid4()
    profile.role = UserRoleEnum.student
    profile.is_onboarded = False
    return profile


@pytest.fixture
def parent_profile():
    profile = MagicMock(spec=UserProfile)
    profile.id = uuid4()
    profile.role = UserRoleEnum.parent
    return profile


# ── get_my_profile ────────────────────────────────────────────────────────────

class TestGetMyProfile:
    async def test_returns_profile_when_found(self, service, db, student_profile):
        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=student_profile)

            result = await service.get_my_profile(db, student_profile.id)

            assert result == student_profile
            mock_repo.get_by_id.assert_awaited_once_with(db, student_profile.id)

    async def test_raises_not_found_when_profile_missing(self, service, db):
        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(NotFound):
                await service.get_my_profile(db, uuid4())


# ── update_my_profile ─────────────────────────────────────────────────────────

class TestUpdateMyProfile:
    async def test_updates_provided_fields_only(self, service, db, student_profile):
        updated = MagicMock(spec=UserProfile)
        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.update = AsyncMock(return_value=updated)

            data = UpdateProfileRequest(school_name="Springfield Elementary")
            result = await service.update_my_profile(db, student_profile.id, data)

            assert result == updated
            mock_repo.update.assert_awaited_once_with(
                db, student_profile.id, {"school_name": "Springfield Elementary"}
            )

    async def test_returns_current_profile_when_no_fields_provided(
        self, service, db, student_profile
    ):
        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=student_profile)
            mock_repo.update = AsyncMock()

            data = UpdateProfileRequest()  # all None / unset
            result = await service.update_my_profile(db, student_profile.id, data)

            assert result == student_profile
            mock_repo.update.assert_not_awaited()

    async def test_raises_not_found_when_profile_missing(self, service, db):
        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.update = AsyncMock(return_value=None)

            data = UpdateProfileRequest(full_name="Alice")
            with pytest.raises(NotFound):
                await service.update_my_profile(db, uuid4(), data)


# ── complete_profile ──────────────────────────────────────────────────────────

class TestCompleteProfile:
    async def test_sets_is_onboarded_true(self, service, db, student_profile):
        updated = MagicMock(spec=UserProfile)
        updated.is_onboarded = True

        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=student_profile)
            mock_repo.update = AsyncMock(return_value=updated)
            query_result = MagicMock()
            query_result.fetchall.return_value = []
            db.execute.return_value = query_result

            data = CompleteProfileRequest(
                school_name="City School",
                district="Pune",
                std_class=5,
            )
            result = await service.complete_profile(db, student_profile.id, data)

            assert result == updated
            call_args = mock_repo.update.call_args
            updates_passed = call_args[0][2]  # 3rd positional arg
            assert updates_passed["is_onboarded"] is True

    async def test_student_without_std_class_raises_bad_request(
        self, service, db, student_profile
    ):
        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=student_profile)

            data = CompleteProfileRequest(
                school_name="City School",
                district="Pune",
                std_class=None,  # missing for student
            )
            with pytest.raises(BadRequest, match="std_class"):
                await service.complete_profile(db, student_profile.id, data)

    async def test_parent_can_complete_profile_without_std_class(
        self, service, db, parent_profile
    ):
        updated = MagicMock(spec=UserProfile)
        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=parent_profile)
            mock_repo.update = AsyncMock(return_value=updated)

            data = CompleteProfileRequest(
                school_name="N/A",
                district="Mumbai",
                # no std_class — allowed for parents
            )
            result = await service.complete_profile(db, parent_profile.id, data)
            assert result == updated

    async def test_raises_not_found_when_profile_missing(self, service, db):
        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)

            data = CompleteProfileRequest(school_name="X", district="Y", std_class=5)
            with pytest.raises(NotFound):
                await service.complete_profile(db, uuid4(), data)


# ── link_child ────────────────────────────────────────────────────────────────

class TestLinkChild:
    @pytest.fixture
    def student(self):
        s = MagicMock(spec=UserProfile)
        s.id = uuid4()
        s.role = UserRoleEnum.student
        return s

    async def test_creates_link_successfully(self, service, db, student):
        parent_id = uuid4()
        new_link = MagicMock(spec=ParentStudentLink)

        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_user_id_by_email = AsyncMock(return_value=student.id)
            mock_repo.get_by_id = AsyncMock(return_value=student)
            mock_repo.get_link = AsyncMock(return_value=None)
            mock_repo.create_link = AsyncMock(return_value=new_link)

            data = LinkChildRequest(email="student@example.com")
            result = await service.link_child(db, parent_id, data)

            assert result == new_link
            mock_repo.create_link.assert_awaited_once()

    async def test_raises_not_found_when_email_not_registered(
        self, service, db
    ):
        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_user_id_by_email = AsyncMock(return_value=None)

            data = LinkChildRequest(email="ghost@example.com")
            with pytest.raises(NotFound):
                await service.link_child(db, uuid4(), data)

    async def test_raises_bad_request_when_target_is_not_student(
        self, service, db, parent_profile
    ):
        non_student = MagicMock(spec=UserProfile)
        non_student.id = uuid4()
        non_student.role = UserRoleEnum.parent  # not a student

        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_user_id_by_email = AsyncMock(return_value=non_student.id)
            mock_repo.get_by_id = AsyncMock(return_value=non_student)

            data = LinkChildRequest(email="another_parent@example.com")
            with pytest.raises(BadRequest, match="student account"):
                await service.link_child(db, parent_profile.id, data)

    async def test_raises_bad_request_on_self_link(self, service, db):
        parent_id = uuid4()
        self_profile = MagicMock(spec=UserProfile)
        self_profile.id = parent_id
        self_profile.role = UserRoleEnum.student  # role passes, but same UUID

        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_user_id_by_email = AsyncMock(return_value=parent_id)
            mock_repo.get_by_id = AsyncMock(return_value=self_profile)

            data = LinkChildRequest(email="self@example.com")
            with pytest.raises(BadRequest, match="own account"):
                await service.link_child(db, parent_id, data)

    async def test_raises_conflict_when_already_linked(self, service, db, student):
        parent_id = uuid4()
        existing_link = MagicMock(spec=ParentStudentLink)
        existing_link.is_active = True

        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_user_id_by_email = AsyncMock(return_value=student.id)
            mock_repo.get_by_id = AsyncMock(return_value=student)
            mock_repo.get_link = AsyncMock(return_value=existing_link)

            data = LinkChildRequest(email="student@example.com")
            with pytest.raises(Conflict):
                await service.link_child(db, parent_id, data)

    async def test_reactivates_inactive_link(self, service, db, student):
        parent_id = uuid4()
        existing_link = MagicMock(spec=ParentStudentLink)
        existing_link.id = 42
        existing_link.is_active = False
        reactivated = MagicMock(spec=ParentStudentLink)

        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.get_user_id_by_email = AsyncMock(return_value=student.id)
            mock_repo.get_by_id = AsyncMock(return_value=student)
            mock_repo.get_link = AsyncMock(return_value=existing_link)
            mock_repo.update_link = AsyncMock(return_value=reactivated)

            data = LinkChildRequest(email="student@example.com")
            result = await service.link_child(db, parent_id, data)

            assert result == reactivated
            mock_repo.update_link.assert_awaited_once_with(
                db, 42, {"is_active": True}
            )


# ── update_my_profile — is_onboarded via PUT /me ─────────────────────────────

class TestUpdateProfileIsOnboarded:
    """User spec: test_update_profile_sets_is_onboarded_true."""

    async def test_sets_is_onboarded_true(self, service, db, student_profile):
        updated = MagicMock(spec=UserProfile)
        updated.is_onboarded = True

        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.update = AsyncMock(return_value=updated)

            data = UpdateProfileRequest(is_onboarded=True)
            result = await service.update_my_profile(db, student_profile.id, data)

            assert result == updated
            call_args = mock_repo.update.call_args
            updates_passed = call_args[0][2]
            assert updates_passed["is_onboarded"] is True

    async def test_partial_update_preserves_unchanged_fields(self, service, db, student_profile):
        """User spec: test_update_profile_partial_update.
        Only send full_name — phone should remain unchanged."""
        updated = MagicMock(spec=UserProfile)
        updated.full_name = "Alice Updated"
        updated.phone = "9876543210"  # unchanged

        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.update = AsyncMock(return_value=updated)

            data = UpdateProfileRequest(full_name="Alice Updated")
            result = await service.update_my_profile(db, student_profile.id, data)

            # Only full_name should be in the updates dict (exclude_unset)
            call_args = mock_repo.update.call_args
            updates_passed = call_args[0][2]
            assert "full_name" in updates_passed
            assert "phone" not in updates_passed
            assert result.full_name == "Alice Updated"
            assert result.phone == "9876543210"


# ── update_my_profile — validation ───────────────────────────────────────────

class TestUpdateProfileValidation:
    """User spec: test_update_profile_invalid_language."""

    def test_invalid_language_raises_validation_error(self):
        """preferred_language only accepts 'en', 'mr', 'hi'."""
        with pytest.raises(ValidationError, match="preferred_language"):
            UpdateProfileRequest(preferred_language="jp")

    def test_valid_language_accepted(self):
        """Confirm valid languages pass."""
        for lang in ("en", "mr", "hi"):
            req = UpdateProfileRequest(preferred_language=lang)
            assert req.preferred_language == lang


# ── change_password ──────────────────────────────────────────────────────────

class TestChangePassword:
    """User spec: change_password error paths."""

    async def test_wrong_current_password_raises_bad_request(self, service):
        """User spec: test_change_password_wrong_current_password."""
        data = ChangePasswordRequest(
            current_password="wrong_password",
            new_password="newpass1234",
            confirm_password="newpass1234",
        )

        with patch("app.modules.user.service.create_client") as mock_create:
            mock_supabase = MagicMock()

            # Step 1 succeeds (get user)
            mock_user_resp = MagicMock()
            mock_user_resp.user.email = "test@example.com"
            mock_supabase.auth.admin.get_user_by_id.return_value = mock_user_resp

            # Step 2 fails (sign-in with wrong password)
            mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login")

            mock_create.return_value = mock_supabase

            with pytest.raises(BadRequest, match="Current password is incorrect"):
                await service.change_password(uuid4(), data)

    def test_passwords_dont_match_raises_value_error(self):
        """User spec: test_change_password_passwords_dont_match.
        Pydantic validator should catch mismatched passwords."""
        with pytest.raises(ValidationError, match="Passwords do not match"):
            ChangePasswordRequest(
                current_password="current123",
                new_password="newpass1234",
                confirm_password="differentpass",
            )


# ── update_avatar ────────────────────────────────────────────────────────────

class TestUpdateAvatar:
    """User spec: test_avatar_url_updated_correctly."""

    async def test_updates_avatar_url(self, service, db):
        user_id = uuid4()
        new_url = "https://example.com/avatar.jpg"

        updated_profile = MagicMock(spec=UserProfile)
        updated_profile.avatar_url = new_url

        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.update = AsyncMock(return_value=updated_profile)

            result = await service.update_avatar(db, user_id, new_url)

            assert result.avatar_url == new_url
            mock_repo.update.assert_awaited_once_with(
                db, user_id, {"avatar_url": new_url}
            )

    async def test_raises_not_found_for_missing_user(self, service, db):
        with patch("app.modules.user.service.user_repository") as mock_repo:
            mock_repo.update = AsyncMock(return_value=None)

            with pytest.raises(NotFound):
                await service.update_avatar(db, uuid4(), "https://example.com/a.jpg")
