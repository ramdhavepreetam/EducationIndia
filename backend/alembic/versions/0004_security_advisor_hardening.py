"""Apply Supabase security advisor hardening.

Revision ID: 0004_security_advisor_hardening
Revises: 0003_multi_select_questions
Create Date: 2026-05-13
"""

from alembic_helpers import execute_sql_script, sql_file

revision = "0004_security_advisor_hardening"
down_revision = "0003_multi_select_questions"
branch_labels = None
depends_on = None

def upgrade() -> None:
    execute_sql_script(sql_file("migration_security_advisor_20260430.sql"))


def downgrade() -> None:
    raise NotImplementedError("Security hardening migration is not safely reversible.")
