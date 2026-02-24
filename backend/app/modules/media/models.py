"""
Media module models — tracks uploaded files (images, etc.).
Provider-agnostic: file_url points to local /static/ path or CDN URL depending on provider.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, TIMESTAMP

from app.database import Base


class MediaFile(Base):
    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True)
    # Who uploaded
    uploaded_by = Column(String(36), nullable=True)  # UUID as string (auth.users)
    # What it is: 'question_image', 'option_image', 'avatar'
    file_type = Column(String(50), nullable=False)
    # Original filename for reference
    original_filename = Column(String(255), nullable=False)
    # Stored path / CDN key (provider-specific)
    storage_key = Column(Text, nullable=False)
    # Public URL returned to clients
    file_url = Column(Text, nullable=False)
    # MIME type
    content_type = Column(String(100), nullable=True)
    # File size in bytes
    file_size = Column(Integer, nullable=True)
    # Soft delete
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()")
