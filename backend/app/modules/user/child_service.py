from uuid import UUID
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.exceptions import BadRequest, NotFound, Forbidden
from app.modules.user.child_schemas import ChildProfileSchema, CreateChildRequest, UpdateChildRequest
from app.modules.user.child_repository import ChildRepository

class ChildService:
    def __init__(self):
        self.repo = ChildRepository()

    async def get_children(self, parent_id: UUID, db: AsyncSession) -> List[ChildProfileSchema]:
        children = await self.repo.get_children(parent_id, db)
        return [ChildProfileSchema.model_validate(c) for c in children]

    async def get_child(self, child_id: UUID, parent_id: UUID, db: AsyncSession) -> ChildProfileSchema:
        child = await self.repo.get_by_id(child_id, parent_id, db)
        if not child:
            raise NotFound("Child profile not found")
        return ChildProfileSchema.model_validate(child)

    async def create_child(self, parent_id: UUID, data: CreateChildRequest, db: AsyncSession) -> ChildProfileSchema:
        existing = await self.repo.get_children(parent_id, db)
        if len(existing) >= 10:
            raise BadRequest("Maximum 10 child profiles allowed")
        child = await self.repo.create(parent_id, data, db)
        return ChildProfileSchema.model_validate(child)

    async def update_child(self, child_id: UUID, parent_id: UUID, data: UpdateChildRequest, db: AsyncSession) -> ChildProfileSchema:
        child = await self.repo.get_by_id(child_id, parent_id, db)
        if not child:
            raise NotFound("Child profile not found")
        updated_child = await self.repo.update(child_id, parent_id, data, db)
        return ChildProfileSchema.model_validate(updated_child)

    async def delete_child(self, child_id: UUID, parent_id: UUID, db: AsyncSession) -> bool:
        child = await self.repo.get_by_id(child_id, parent_id, db)
        if not child:
            raise NotFound("Child profile not found")
        return await self.repo.deactivate(child_id, parent_id, db)
