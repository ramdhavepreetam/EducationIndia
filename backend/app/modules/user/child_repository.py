from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import ChildProfile
from app.modules.user.child_schemas import CreateChildRequest, UpdateChildRequest

class ChildRepository:
    async def get_children(self, parent_id: UUID, db: AsyncSession) -> list[ChildProfile]:
        """All active child profiles for this parent."""
        stmt = select(ChildProfile).where(
            ChildProfile.parent_id == parent_id,
            ChildProfile.is_active == True
        ).order_by(ChildProfile.created_at)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, child_id: UUID, parent_id: UUID, db: AsyncSession) -> Optional[ChildProfile]:
        """Single child. Validates parent owns it."""
        stmt = select(ChildProfile).where(
            ChildProfile.id == child_id,
            ChildProfile.parent_id == parent_id,
            ChildProfile.is_active == True
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, parent_id: UUID, data: CreateChildRequest, db: AsyncSession) -> ChildProfile:
        child = ChildProfile(
            parent_id=parent_id,
            name=data.name,
            std_class=data.std_class,
            medium=data.medium,
            school_name=data.school_name,
            district=data.district,
            avatar_color=data.avatar_color,
        )
        db.add(child)
        await db.commit()
        await db.refresh(child)
        return child

    async def update(self, child_id: UUID, parent_id: UUID, data: UpdateChildRequest, db: AsyncSession) -> ChildProfile:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(child_id, parent_id, db)

        stmt = (
            update(ChildProfile)
            .where(ChildProfile.id == child_id, ChildProfile.parent_id == parent_id)
            .values(**update_data)
            .returning(ChildProfile)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one()

    async def deactivate(self, child_id: UUID, parent_id: UUID, db: AsyncSession) -> bool:
        """Soft delete — sets is_active=False."""
        stmt = (
            update(ChildProfile)
            .where(ChildProfile.id == child_id, ChildProfile.parent_id == parent_id)
            .values(is_active=False)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    async def validate_ownership(self, child_profile_id: UUID, parent_id: UUID, db: AsyncSession) -> bool:
        """Returns True if this child belongs to this parent."""
        child = await self.get_by_id(child_profile_id, parent_id, db)
        return child is not None


child_repository = ChildRepository()
