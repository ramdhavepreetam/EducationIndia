# ADR-008: Database Platform Selection

**Date:** 2025-02-21
**Status:** Accepted
**Decider:** Preetam
**Modules Affected:** All (foundational infrastructure decision)

---

## Context

ScholarPath needs a relational database that can handle: complex joins between
questions, contexts, options and responses; row-level security for multi-role
access; triggers for stats updates; and full-text search on questions in future.
The project starts free and must scale without re-architecture. Auth, storage,
and database should ideally integrate cleanly. The team is comfortable with
PostgreSQL from previous projects.

---

## Decision

We will use Supabase as the managed PostgreSQL platform. Supabase provides
PostgreSQL with full SQL access, Row Level Security, triggers, functions,
built-in Auth (covered in ADR-001), and Storage — all on one free tier
(500MB database, 1GB storage). Local development uses the Supabase CLI
with a local Docker PostgreSQL instance.

---

## Alternatives Considered

### Option 1: Raw PostgreSQL on Render
Self-managed PostgreSQL on Render free tier.
- Pro: Direct control, no platform dependency
- Con: No built-in auth integration, no RLS helpers
- Con: Render free PostgreSQL tier has 90-day expiry limitation

### Option 2: PlanetScale (MySQL)
Serverless MySQL with branching.
- Pro: Excellent DX, serverless scaling
- Con: MySQL — losing PostgreSQL-specific features (JSONB, arrays, GIN indexes)
- Con: No row-level security native to MySQL

### Option 3: Supabase ← CHOSEN
Managed PostgreSQL with batteries included.
- Pro: 500MB free, no 90-day expiry
- Pro: Auth + DB + Storage in one platform (ADR-001 uses Supabase Auth)
- Pro: RLS policies integrate with auth.uid() natively
- Pro: DB triggers work out of the box
- Pro: JSONB, arrays, GIN indexes — full PostgreSQL power
- Con: Supabase free tier pauses after 1 week of inactivity
- Con: 500MB limit requires monitoring (1000+ questions + attempts will grow)

---

## Consequences

### Positive
- One dashboard for DB + Auth + Storage
- RLS policies written once, enforced at DB level (not just application)
- DB triggers handle stats updates automatically (no application code needed)
- Supabase CLI enables local development with identical PostgreSQL version

### Negative
- Free tier pauses project after 7 days inactivity — unacceptable for production
  → Set up a free cron ping (e.g. UptimeRobot) to prevent pausing
- 500MB limit: ~100,000 exam responses ≈ ~50MB, so plenty for launch phase
- Platform dependency — migration to raw PostgreSQL requires export + reimport

### Neutral
- FastAPI connects to Supabase via standard PostgreSQL connection string
- SQLAlchemy used for ORM — not Supabase client library — keeps backend portable
- Supabase JS client used in React frontend for auth only (not data fetching)
- All data fetching goes through FastAPI, not direct Supabase REST/GraphQL

---

## Module Impact

```
database.py              → SQLAlchemy engine using DATABASE_URL (standard postgres:// URL)
config.py                → SUPABASE_URL, SUPABASE_SERVICE_KEY for auth verification
auth/dependencies.py     → verify_token() uses Supabase JWT secret
All models               → Standard SQLAlchemy models — no Supabase-specific ORM
Migration SQL            → Run once in Supabase SQL Editor (scholarpath_migration.sql)
.env.example             → DATABASE_URL, SUPABASE_URL, SUPABASE_ANON_KEY documented
```

---

## Implementation Notes

Preventing free tier pauses:
- Set up UptimeRobot (free) to ping API health endpoint every 5 minutes
- GET /api/health → returns 200, keeps Supabase project active

Storage monitoring query (run monthly):
```sql
SELECT
    pg_size_pretty(pg_database_size(current_database())) as db_size,
    (SELECT COUNT(*) FROM responses) as total_responses,
    (SELECT COUNT(*) FROM attempts) as total_attempts,
    (SELECT COUNT(*) FROM questions) as total_questions;
```

Local dev setup:
```bash
npm install -g supabase
supabase init
supabase start          # Starts local PostgreSQL on port 54322
# Run scholarpath_migration.sql against local instance
supabase db reset       # Resets + re-runs migration + seed
```

---

## Review Trigger

Revisit when database size approaches 400MB (buffer before 500MB limit) —
evaluate Supabase Pro ($25/month) vs. migrating to managed PostgreSQL on
Railway or Render. Revisit when project gets consistent daily traffic —
free tier pause-prevention becomes critical.
