"""Content integrity guards for the question bank.

Adds NOT VALID CHECK constraints preventing new unanswerable questions
(missing stem, image-typed question without an image, blank option) and a
v_paper_health admin view surfacing existing defects per paper.

Constraints are NOT VALID by design — a 2026-08-17 audit found 396 image
questions with no image and 375 questions whose correct answer is a blank
option, so a validating constraint could not be added without first destroying
or repairing real content. NOT VALID blocks new bad data immediately.

Wraps database/migration_content_integrity_guards.sql, which is idempotent
(DROP CONSTRAINT IF EXISTS / CREATE OR REPLACE VIEW).

Revision ID: 0008_content_integrity
Revises: 0007_cancelled_questions
Create Date: 2026-08-17
"""

from alembic import op

from alembic_helpers import execute_sql_script, sql_file

revision = "0008_content_integrity"
down_revision = "0007_cancelled_questions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    execute_sql_script(sql_file("migration_content_integrity_guards.sql"))


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_paper_health")
    op.execute(
        "ALTER TABLE options DROP CONSTRAINT IF EXISTS options_content_present_chk"
    )
    op.execute(
        "ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_image_type_has_image_chk"
    )
    op.execute(
        "ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_stem_present_chk"
    )
