"""Add scoped subscription entitlements.

Revision ID: 0005_scoped_subs
Revises: 0004_security_advisor_hardening
Create Date: 2026-05-13
"""

from alembic_helpers import execute_sql_script, sql_file

revision = "0005_scoped_subs"
down_revision = "0004_security_advisor_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    execute_sql_script(sql_file("migration_scoped_subscription_entitlements.sql"))


def downgrade() -> None:
    raise NotImplementedError("Scoped subscription entitlement migration is not safely reversible.")
