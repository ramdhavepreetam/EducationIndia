"""Apply ADR-013 child profiles and ADR-014 payments schema.

Revision ID: 0002_adr013_014
Revises: 0001_baseline
Create Date: 2026-05-13
"""

from alembic_helpers import execute_sql_script, sql_file

revision = "0002_adr013_014"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

def upgrade() -> None:
    execute_sql_script(sql_file("migration_adr013_014.sql"))


def downgrade() -> None:
    raise NotImplementedError("ADR-013/014 migration is not safely reversible.")
