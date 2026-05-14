# Database Migrations

Alembic is now the canonical migration ledger for ScholarPath.

## Existing Database

The current Supabase database was created before Alembic. It should be stamped
at the baseline revision, then upgraded to the latest tracked migration:

```bash
cd backend
.venv/bin/alembic stamp 0001_baseline
.venv/bin/alembic upgrade head
```

## Fresh Database

For a new Supabase project:

1. Apply the cleaned initial schema from `database/scholarpath_migration.sql`
   in the Supabase SQL Editor.
2. Stamp the baseline:

```bash
cd backend
.venv/bin/alembic stamp 0001_baseline
```

3. Apply the tracked follow-up migrations:

```bash
.venv/bin/alembic upgrade head
```

The initial SQL file contains historical planning text before the executable
schema section, so it is intentionally tracked as a baseline instead of being
executed automatically.

## New Changes

Create a new revision:

```bash
cd backend
.venv/bin/alembic revision -m "describe change"
```

Then put the schema change in `upgrade()` and the reversal in `downgrade()` when
the reversal is safe. Do not add new standalone SQL files outside Alembic.

## Current Chain

- `0001_baseline`
- `0002_adr013_014`
- `0003_multi_select_questions`
- `0004_security_advisor_hardening`
- `0005_scoped_subs`
