# ScholarPath Alembic Migrations

Alembic is the canonical migration ledger from this point forward.

The original Supabase schema was created before Alembic and is tracked as a
baseline revision (`0001_baseline`). For an existing
database that already has `database/scholarpath_migration.sql` applied, stamp
the baseline first:

```bash
cd backend
.venv/bin/alembic stamp 0001_baseline
.venv/bin/alembic upgrade head
```

For a brand-new Supabase database, apply the cleaned initial schema manually in
the Supabase SQL Editor first, then run the same stamp/upgrade commands. The
initial SQL file currently contains historical prompt text before the executable
schema section, so it is intentionally not executed automatically by Alembic.

New database changes should be added as Alembic revisions instead of standalone
SQL files.
