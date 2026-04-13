"""
User module service — business logic layer.

Rules (CLAUDE.md):
  - Call repository methods only; never write SQL here.
  - Never import from auth module internals — only auth.dependencies.
  - Parent cannot edit student profile — enforced here (not in router).
  - is_onboarded can be set to True via update_my_profile (unified endpoint).
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from supabase import create_client

from app.config import settings
from app.modules.user.models import ParentStudentLink, UserProfile, UserRoleEnum
from app.modules.user.repository import user_repository
from app.modules.user.schemas import (
    ChangePasswordRequest,
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
        Also used for onboarding: client sends { is_onboarded: true, ... }.

        Side-effect (ADR-014):
          If std_class changes, old system-auto-assigned exams are deactivated
          and new exams for the new grade are auto-assigned.
        """
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return await self.get_my_profile(db, user_id)

        # Detect std_class change to trigger re-assignment
        new_std_class = updates.get("std_class")
        if new_std_class is not None:
            current = await user_repository.get_by_id(db, user_id)
            if current and current.std_class != new_std_class:
                await self._swap_grade_assignments(db, user_id, new_std_class)

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

        Side-effect (ADR-014):
          If std_class is provided, auto-assign all active exams for that grade.
        """
        profile = await user_repository.get_by_id(db, user_id)
        if not profile:
            raise NotFound("Profile not found")

        if profile.role == UserRoleEnum.student and data.std_class is None:
            raise BadRequest("std_class is required for student accounts")

        updates = data.model_dump(exclude_unset=True)
        updates["is_onboarded"] = True  # always flip, regardless of what was sent

        updated = await user_repository.update(db, user_id, updates)

        # Auto-assign active exams for student's grade on first onboarding (ADR-014)
        std_class = data.std_class or (profile.std_class if profile.role == UserRoleEnum.student else None)
        if std_class and not profile.is_onboarded:
            await self._assign_grade_exams(db, user_id, std_class)

        return updated  # type: ignore[return-value]

    async def update_avatar(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        avatar_url: str,
    ) -> UserProfile:
        """Update avatar_url on user profile after successful media upload."""
        profile = await user_repository.update(
            db, user_id, {"avatar_url": avatar_url}
        )
        if not profile:
            raise NotFound("Profile not found")
        return profile

    async def change_password(
        self,
        user_id: uuid.UUID,
        data: ChangePasswordRequest,
    ) -> dict:
        """
        Uses Supabase admin client to update password.
        Validates current_password by attempting a sign-in first.

        IMPORTANT: Supabase handles password storage — this NEVER
        touches passwords in the DB directly.
        """
        supabase_client = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
        )

        # Step 1: Get user email from auth.users
        try:
            user_resp = supabase_client.auth.admin.get_user_by_id(str(user_id))
            email = user_resp.user.email
        except Exception:
            raise BadRequest("Unable to verify identity")

        # Step 2: Verify current password via Supabase sign-in
        try:
            supabase_client.auth.sign_in_with_password({
                "email": email,
                "password": data.current_password,
            })
        except Exception:
            raise BadRequest("Current password is incorrect")

        # Step 3: Update password via admin API
        try:
            supabase_client.auth.admin.update_user_by_id(
                str(user_id),
                {"password": data.new_password},
            )
        except Exception:
            raise BadRequest("Password update failed. Try again.")

        return {"success": True}

    async def get_subscription_status(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> dict:
        """
        Convenience wrapper that returns subscription status for a parent.
        Uses access_control.get_access_context() as the single source of truth.
        """
        from app.shared.access_control import get_access_context

        ctx = await get_access_context(db, user_id)
        return {
            "is_paid": ctx.get("is_paid", False),
            "expires_at": ctx.get("expires_at"),
            "days_remaining": ctx.get("days_remaining", 0),
        }

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


    # ── Private helpers ───────────────────────────────────────────────────────

    async def _assign_grade_exams(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
        std_class: int,
    ) -> None:
        """
        Auto-assign all active exams matching std_class to this student.
        Called on first onboarding. Uses attempt_repository to stay within
        module boundaries (attempt module owns exam_assignments).
        """
        from sqlalchemy import text
        from app.modules.attempt.repository import attempt_repository

        result = await db.execute(
            text(
                "SELECT e.id FROM exams e "
                "JOIN exam_events ev ON ev.id = e.event_id "
                "WHERE e.is_active = true AND ev.std_class = :cls"
            ),
            {"cls": std_class},
        )
        exam_ids = [row[0] for row in result.fetchall()]
        if not exam_ids:
            return

        rows = [{"exam_id": eid, "student_id": student_id} for eid in exam_ids]
        await attempt_repository.bulk_create_assignments(db, rows)
        await db.commit()

    async def _swap_grade_assignments(
        self,
        db: AsyncSession,
        student_id: uuid.UUID,
        new_std_class: int,
    ) -> None:
        """
        Called when std_class changes:
          1. Deactivate all system-auto-assigned rows (assigned_by IS NULL)
          2. Assign active exams for the new grade
        Manually-assigned rows (assigned_by IS NOT NULL) are untouched.
        """
        from app.modules.attempt.repository import attempt_repository

        await attempt_repository.deactivate_auto_assignments_for_student(db, student_id)
        await self._assign_grade_exams(db, student_id, new_std_class)


# Module-level singleton — import this in router.py
user_service = UserService()
