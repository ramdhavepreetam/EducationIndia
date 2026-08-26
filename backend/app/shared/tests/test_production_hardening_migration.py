from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


def _migration_sql() -> str:
    return (REPO_ROOT / "database" / "migration_production_hardening.sql").read_text(
        encoding="utf-8"
    )


def test_alembic_wires_production_hardening_migration():
    revision = (
        REPO_ROOT
        / "backend"
        / "alembic"
        / "versions"
        / "0006_production_hardening.py"
    ).read_text(encoding="utf-8")

    assert 'revision = "0006_prod_hardening"' in revision
    assert 'down_revision = "0005_scoped_subs"' in revision
    assert 'sql_file("migration_production_hardening.sql")' in revision


def test_migration_removes_public_raw_answer_table_access():
    sql = _migration_sql()

    assert 'DROP POLICY IF EXISTS "Anyone reads questions for active exams"' in sql
    assert 'DROP POLICY IF EXISTS "Anyone reads options"' in sql
    assert "REVOKE SELECT ON public.questions FROM anon, authenticated" in sql
    assert "REVOKE SELECT ON public.options FROM anon, authenticated" in sql
    assert "REVOKE SELECT ON public.v_exam_answers FROM anon, authenticated" in sql


def test_migration_supports_child_profile_attempts_and_media_table():
    sql = _migration_sql()

    assert "ALTER COLUMN student_id DROP NOT NULL" in sql
    assert "attempts_has_owner_check" in sql
    assert "CREATE TABLE IF NOT EXISTS public.media_files" in sql
    assert "ALTER TABLE public.media_files ENABLE ROW LEVEL SECURITY" in sql


def test_question_stats_trigger_no_longer_depends_on_response_is_correct():
    sql = _migration_sql()
    trigger_sql = sql.split(
        "CREATE OR REPLACE FUNCTION public.update_question_stats_on_submit", 1
    )[1]

    assert "r.is_correct" not in trigger_sql
    assert "selected_options" in trigger_sql
    assert "correct_options" in trigger_sql
    assert "COALESCE(q.is_cancelled, false) = false" in trigger_sql


def test_payment_tables_get_rls_policies():
    sql = _migration_sql()

    assert "ALTER TABLE public.app_settings ENABLE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY" in sql
    assert 'CREATE POLICY "Parents read own subscriptions"' in sql
    assert 'CREATE POLICY "Parents read own payments"' in sql
