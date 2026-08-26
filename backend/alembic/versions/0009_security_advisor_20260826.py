"""Close RLS gaps flagged by the Supabase Security Advisor (2026-08-26).

Two objects in the live database were reachable from the PostgREST-exposed
`anon` role:

  * alembic_version had RLS disabled entirely — this is the table the advisor
    reported as `rls_disabled_in_public`.
  * v_paper_health was created without security_invoker, so as a
    postgres-owned view it ran with the owner's privileges and bypassed RLS
    on every table it reads.

Each fix pairs the RLS/security_invoker change with an explicit REVOKE so the
object stays closed if a future default grant re-opens it.

Wraps database/migration_security_advisor_20260826.sql, which is idempotent.

Revision ID: 0009_security_advisor
Revises: 0008_content_integrity
Create Date: 2026-08-26
"""

from alembic import op

from alembic_helpers import execute_sql_script, sql_file

revision = "0009_security_advisor"
down_revision = "0008_content_integrity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    execute_sql_script(sql_file("migration_security_advisor_20260826.sql"))


def downgrade() -> None:
    # Deliberately does not re-grant anon/authenticated access — reopening a
    # closed security hole is never the safe direction for a downgrade.
    op.execute("ALTER VIEW public.v_paper_health RESET (security_invoker)")
    op.execute("ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY")
