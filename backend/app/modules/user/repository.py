"""
User module repository — ALL database queries live here.

CLAUDE.md rule: services call repository, never execute queries directly.
Routers call services, never call repository directly.
"""

import uuid

from sqlalchemy import select, text, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.user.models import ParentStudentLink, UserProfile


class UserRepository:

    # ── UserProfile queries ───────────────────────────────────────────────────

    async def get_by_id(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> UserProfile | None:
        result = await db.execute(
            select(UserProfile).where(
                UserProfile.id == user_id,
                UserProfile.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_id_by_email(
        self, db: AsyncSession, email: str
    ) -> uuid.UUID | None:
        """
        Look up a user's UUID from auth.users by email.
        Cross-schema query — auth.users is managed by Supabase, not our ORM.
        Uses parameterised query; safe from injection.
        """
        result = await db.execute(
            text("SELECT id FROM auth.users WHERE email = :email"),
            {"email": email.lower().strip()},
        )
        row = result.first()
        return row[0] if row else None

    async def update(
        self, db: AsyncSession, user_id: uuid.UUID, updates: dict
    ) -> UserProfile | None:
        """Apply a dict of column updates, then return the refreshed profile."""
        await db.execute(
            sa_update(UserProfile)
            .where(UserProfile.id == user_id)
            .values(**updates)
        )
        await db.flush()
        return await self.get_by_id(db, user_id)

    # ── ParentStudentLink queries ─────────────────────────────────────────────

    async def get_children_with_links(
        self, db: AsyncSession, parent_id: uuid.UUID
    ) -> list[ParentStudentLink]:
        """
        Return active links for a parent, with student profile eagerly loaded.
        Uses selectinload to avoid N+1 queries.
        """
        result = await db.execute(
            select(ParentStudentLink)
            .options(selectinload(ParentStudentLink.student))
            .where(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def get_link(
        self, db: AsyncSession, parent_id: uuid.UUID, student_id: uuid.UUID
    ) -> ParentStudentLink | None:
        """Find any link (active or inactive) between this parent and student."""
        result = await db.execute(
            select(ParentStudentLink).where(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_link(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID,
        student_id: uuid.UUID,
        child_nickname: str | None = None,
        linked_by: uuid.UUID | None = None,
    ) -> ParentStudentLink:
        link = ParentStudentLink(
            parent_id=parent_id,
            student_id=student_id,
            child_nickname=child_nickname,
            linked_by=linked_by,
            is_active=True,
        )
        db.add(link)
        await db.flush()
        await db.refresh(link)
        return link

    async def update_link(
        self, db: AsyncSession, link_id: int, updates: dict
    ) -> ParentStudentLink:
        """Reactivate or update an existing link."""
        await db.execute(
            sa_update(ParentStudentLink)
            .where(ParentStudentLink.id == link_id)
            .values(**updates)
        )
        await db.flush()
        result = await db.execute(
            select(ParentStudentLink).where(ParentStudentLink.id == link_id)
        )
        return result.scalar_one()


# Module-level singleton — import this in service.py
user_repository = UserRepository()
