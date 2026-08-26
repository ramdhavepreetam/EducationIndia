"""Apply production hardening fixes.

Revision ID: 0006_prod_hardening
Revises: 0005_scoped_subs
Create Date: 2026-07-01
"""

from alembic_helpers import execute_sql_script, sql_file

revision = "0006_prod_hardening"
down_revision = "0005_scoped_subs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    execute_sql_script(sql_file("migration_production_hardening.sql"))


def downgrade() -> None:
    raise NotImplementedError("Production hardening migration is not safely reversible.")
