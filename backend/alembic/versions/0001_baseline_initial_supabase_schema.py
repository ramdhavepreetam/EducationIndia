"""Baseline existing initial Supabase schema.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-05-13

This revision represents the original schema from database/scholarpath_migration.sql.
That file was applied manually before Alembic was introduced and is not a clean
executable migration file because it contains historical planning text before
the SQL schema section.
"""

from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    raise NotImplementedError("Initial schema baseline cannot be downgraded safely.")
