"""
User module service — business logic layer.

Rules (CLAUDE.md):
  - Call repository methods only; never write SQL here.
  - Never import from auth module internals — only auth.dependencies.
  - Parent cannot edit student profile — enforced here (not in router).
  - is_onboarded flips to True exactly once: in complete_profile().
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import ParentStudentLink, UserProfile, UserRoleEnum
from app.modules.user.repository import user_repository
from app.modules.user.schemas import (
    CompleteProfileRequest,
    LinkChildRequest,
    UpdateProfileRequest,
)
from app.shared.exceptions import BadRequest, Conflict, NotFound


class UserService:

    async def get_my_profile(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> UserProfile:
        profile = await user_repository.get_by_id(db, user_id)
        if not profile:
            raise NotFound("Profile not found")
        return profile

    async def update_my_profile(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        data: UpdateProfileRequest,
    ) -> UserProfile:
        """
        Partial update — only fields present in the request body are changed.
        Uses exclude_unset so missing fields are not overwritten with None.
        """
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            # Nothing to change — return current state
            return await self.get_my_profile(db, user_id)

        profile = await user_repository.update(db, user_id, updates)
        if not profile:
            raise NotFound("Profile not found")
        return profile

    async def complete_profile(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        data: CompleteProfileRequest,
    ) -> UserProfile:
        """
        Onboarding step — sets is_onboarded = True.
        std_class is required for student accounts.
        Safe to call more than once (idempotent apart from overwriting fields).
        """
        profile = await user_repository.get_by_id(db, user_id)
        if not profile:
            raise NotFound("Profile not found")

        if profile.role == UserRoleEnum.student and data.std_class is None:
            raise BadRequest("std_class is required for student accounts")

        updates = data.model_dump(exclude_unset=True)
        updates["is_onboarded"] = True  # always flip, regardless of what was sent

        updated = await user_repository.update(db, user_id, updates)
        return updated  # type: ignore[return-value]  # profile existed, so update returns it

    async def get_my_children(
        self, db: AsyncSession, parent_id: uuid.UUID
    ) -> list[ParentStudentLink]:
        """
        Returns active parent→student links with student profile loaded.
        Router is guarded by require_parent so caller is always a parent.
        """
        return await user_repository.get_children_with_links(db, parent_id)

    async def link_child(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID,
        data: LinkChildRequest,
    ) -> ParentStudentLink:
        """
        Parent self-service linking (ADR-009 Option B).

        Flow:
          1. Find student UUID from auth.users by email
          2. Verify the account has role = student
          3. Prevent self-linking
          4. If link exists and inactive → reactivate
          5. If link already active → raise Conflict
          6. Otherwise create new link
        """
        # 1. Resolve email → UUID
        student_uuid = await user_repository.get_user_id_by_email(db, data.email)
        if not student_uuid:
            raise NotFound("No account found with that email address")

        # 2. Load student profile
        student = await user_repository.get_by_id(db, student_uuid)
        if not student:
            raise NotFound("No account found with that email address")

        # 3. Confirm role is student
        if student.role != UserRoleEnum.student:
            raise BadRequest("That email does not belong to a student account")

        # 4. Prevent self-linking
        if student_uuid == parent_id:
            raise BadRequest("A parent cannot link to their own account")

        # 5. Check for existing link (active or inactive)
        existing = await user_repository.get_link(db, parent_id, student_uuid)
        if existing:
            if existing.is_active:
                raise Conflict("You are already linked to this student")
            # Inactive link exists — reactivate and update nickname
            update_data: dict = {"is_active": True}
            if data.child_nickname is not None:
                update_data["child_nickname"] = data.child_nickname
            return await user_repository.update_link(db, existing.id, update_data)

        # 6. Create new link
        return await user_repository.create_link(
            db,
            parent_id=parent_id,
            student_id=student_uuid,
            child_nickname=data.child_nickname,
            linked_by=parent_id,
        )


# Module-level singleton — import this in router.py
user_service = UserService()
