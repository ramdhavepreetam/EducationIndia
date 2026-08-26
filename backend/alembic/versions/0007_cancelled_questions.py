"""Support official answer-key cancelled questions.

Adds questions.is_cancelled / cancelled_reason and updates the
sync_correct_option trigger to clear option correctness for cancelled questions.

This wraps database/migration_cancelled_questions.sql, which was previously applied
to Supabase out-of-band without an Alembic revision. The SQL is idempotent
(ADD COLUMN IF NOT EXISTS / CREATE OR REPLACE / DROP TRIGGER IF EXISTS), so this is
a no-op on databases that already have it and brings fresh databases up to date.

Revision ID: 0007_cancelled_questions
Revises: 0006_prod_hardening
Create Date: 2026-08-03
"""

from alembic_helpers import execute_sql_script, sql_file

revision = "0007_cancelled_questions"
down_revision = "0006_prod_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    execute_sql_script(sql_file("migration_cancelled_questions.sql"))


def downgrade() -> None:
    raise NotImplementedError("Cancelled-questions migration is not safely reversible.")
