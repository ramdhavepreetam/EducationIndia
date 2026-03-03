from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class CreateChildRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    std_class: int = Field(..., ge=5, le=8)
    medium: Optional[str] = 'english'
    school_name: Optional[str] = None
    district: Optional[str] = None
    avatar_color: Optional[str] = '#3B82F6'

class UpdateChildRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2)
    std_class: Optional[int] = Field(None, ge=5, le=8)
    medium: Optional[str] = None
    school_name: Optional[str] = None
    district: Optional[str] = None
    avatar_color: Optional[str] = None

class ChildProfileSchema(BaseModel):
    id: UUID
    parent_id: UUID
    name: str
    std_class: int
    medium: Optional[str] = None
    school_name: Optional[str] = None
    district: Optional[str] = None
    avatar_color: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
