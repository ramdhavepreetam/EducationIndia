from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.dependencies import UserIdentity, require_parent
from app.modules.user.child_schemas import ChildProfileSchema, CreateChildRequest, UpdateChildRequest
from app.modules.user.child_service import ChildService

router = APIRouter(prefix="/api/children", tags=["Children"])
child_service = ChildService()

@router.get("", response_model=List[ChildProfileSchema])
async def list_children(
    user: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db)
):
    """List all active child profiles for this parent."""
    return await child_service.get_children(user.id, db)

@router.post("", response_model=ChildProfileSchema, status_code=status.HTTP_201_CREATED)
async def create_child(
    data: CreateChildRequest,
    user: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db)
):
    """Create a new child profile."""
    return await child_service.create_child(user.id, data, db)

@router.get("/{child_id}", response_model=ChildProfileSchema)
async def get_child(
    child_id: UUID,
    user: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db)
):
    """Get a single child profile by ID."""
    return await child_service.get_child(child_id, user.id, db)

@router.put("/{child_id}", response_model=ChildProfileSchema)
async def update_child(
    child_id: UUID,
    data: UpdateChildRequest,
    user: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db)
):
    """Update a child profile."""
    return await child_service.update_child(child_id, user.id, data, db)

@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
    child_id: UUID,
    user: UserIdentity = Depends(require_parent),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a child profile."""
    await child_service.delete_child(child_id, user.id, db)
