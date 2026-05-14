"""Add multi-select question support.

Revision ID: 0003_multi_select_questions
Revises: 0002_adr013_014_child_profiles_payments
Create Date: 2026-05-13
"""

from alembic_helpers import execute_sql_script, sql_file

revision = "0003_multi_select_questions"
down_revision = "0002_adr013_014_child_profiles_payments"
branch_labels = None
depends_on = None

def upgrade() -> None:
    execute_sql_script(sql_file("migration_multi_select.sql"))


def downgrade() -> None:
    raise NotImplementedError("Multi-select migration is not safely reversible.")
