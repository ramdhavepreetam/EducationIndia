"""
conftest.py — sets dummy environment variables required by app.config.Settings
before any test module is imported.

Without this, pydantic-settings raises ValidationError for missing
DATABASE_URL, SUPABASE_URL, etc. when tests import app modules.

Tests that need a real DB use fixtures that override these values.
Unit tests with mocked repos never touch the DB at all.
"""

import os

# Set dummy values before ANY app import happens.
# pytest picks this up as a plugin during collection.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-for-tests-only")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("DEBUG", "true")
