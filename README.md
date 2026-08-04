# ScholarPath

ScholarPath is a multilingual exam-preparation web application for Maharashtra MSCE Scholarship Examination students. It supports 5th and 8th standard practice exams, parent-managed child profiles, admin question management, image-heavy question papers, attempt analysis, and Razorpay-backed premium access.

Production URLs:

- Frontend: https://scholarpath-app.web.app
- Backend: https://scholarpath-backend-470258820905.us-central1.run.app
- Backend alternate Cloud Run URL may be shown by `gcloud run services describe`.

## Current Status

ScholarPath is an active production-oriented build. The main student, parent, admin, question, attempt, analysis, media, and payment flows are implemented. Supabase Security Advisor hardening has been applied through SQL migration.

Recent production fixes included:

- Admin subscription list now shows free parent users as well as paid users.
- Parent premium status refreshes after admin grants access.
- Parent sidebar shows login email to avoid granting premium to the wrong account.
- Parent accounts are limited to two child profiles.
- Admin question editing supports multi-select questions.
- Supabase RLS, view security, extension placement, and function `search_path` hardening have been added.

## Product Scope

Target users:

- Students in 5th and 8th standard preparing for MSCE scholarship exams.
- Parents managing one or two child profiles and reviewing progress.
- Exam admins managing exams, questions, images, subscriptions, and settings.

Supported language architecture:

- English and Marathi are implemented in the schema and UI flow.
- Hindi-ready structure exists through the multilingual column pattern, but Hindi content is not fully populated.

Supported content:

- Text questions
- Image questions
- Context/passages
- Marathi-only questions
- Bilingual questions
- Single-select and multi-select answers
- Image/text options

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 async, Pydantic v2 |
| Database | PostgreSQL on Supabase |
| Auth | Supabase Auth, JWT verification through JWKS/HS256 fallback |
| Frontend | React 18, Vite, Tailwind CSS, Zustand, react-i18next |
| Payments | Razorpay orders, verification, webhooks, manual admin grants |
| Media | Local filesystem provider, Cloudinary/R2-ready provider pattern |
| Charts | Recharts |
| PDF | jsPDF, html2canvas |
| Hosting | Firebase Hosting for frontend, Google Cloud Run for backend |
| Tests | Pytest, Vitest, Testing Library |

## Repository Layout

```text
scholarpath/
├── backend/                  FastAPI app and backend tests
│   ├── app/
│   │   ├── main.py           App factory, middleware, routers, JWKS startup
│   │   ├── config.py         Pydantic settings loaded from .env
│   │   ├── database.py       Async SQLAlchemy engine/session
│   │   ├── modules/          Vertical-slice feature modules
│   │   └── shared/           Exceptions, i18n, access-control helpers
│   ├── Dockerfile            Cloud Run container
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/                 React/Vite app
│   ├── src/modules/          Vertical-slice frontend modules
│   ├── firebase.json         Firebase Hosting config
│   └── package.json
├── database/                 SQL migrations and hardening scripts
├── docs/adr/                 Architecture Decision Records
├── archive/                  Historical one-off seed/import scripts + data (superseded
│                             by backend/app/modules/question/pdf_importer.py)
└── AGENTS.md                 Project knowledge file for coding agents
```

## Architecture

The backend uses vertical-slice modules. Each module owns its own models, schemas, repository, service, and router boundaries where applicable.

| Module | Responsibility |
| --- | --- |
| `auth` | JWT verification and trusted role loading from `user_profiles` |
| `user` | User profiles, parent-child links, child profiles, parent dashboard data |
| `catalog` | Exam boards, categories, events, exams, sections, topics |
| `question` | Question bank, options, contexts, safe delivery, admin editing, bulk import |
| `attempt` | Attempt lifecycle: start, autosave, submit |
| `analysis` | Scoring, topic performance, wrong answers, recommendations |
| `media` | File upload and media provider abstraction |
| `payment` | Plans, subscriptions, payments, Razorpay integration, access status |
| `admin` | Admin orchestration endpoints and dashboards |

Important boundaries:

- Routers should call services or repository only where the module already follows that pattern.
- Repositories own SQL/database access.
- The attempt module stores responses and state; score computation belongs to analysis/scoring logic.
- Exam delivery must never expose correct answers.
- Parent access must always validate ownership through linked child/profile rules.
- Admin bulk import requires admin authentication.

## Backend Routes

Routers are registered in `backend/app/main.py`.

| Prefix | Module | Purpose |
| --- | --- | --- |
| `/api/users` | user | Current user profile, onboarding, avatar, password, child links |
| `/api/parent` | user parent | Parent dashboard, child detail, wrong-answer summaries |
| `/api/children` | user child | Child profile creation/update/delete for parents |
| `/api/catalog` | catalog | Boards, exams, active exams, parent access flags |
| `/api/questions` | question | Safe question delivery and post-submit review |
| `/api/admin/questions` | question admin | Admin question CRUD and bulk import |
| `/api/attempts` | attempt | Start, save, submit, attempt state |
| `/api/analysis` | analysis | Result reports and wrong-answer analysis |
| `/api/media` | media | Admin media upload |
| `/api/admin` | admin | Admin dashboards, settings, payments, subscriptions, publishing |
| `/api/payment` | payment | Plans, payment status, Razorpay order/verify/webhook/history |
| `/health` | app | Health check |

## Frontend Routes

Routes are defined in `frontend/src/App.jsx`.

| Route | Access | Purpose |
| --- | --- | --- |
| `/` | Public | Landing page or role-aware redirect |
| `/login` | Public | Email/password and OAuth login |
| `/register` | Public | Parent registration |
| `/onboarding` | Authenticated | Complete profile/onboarding |
| `/dashboard` | Student | Student dashboard and available exams |
| `/exam/:examId/start` | Student | Exam instructions/start screen |
| `/exam/:examId/attempt` | Student | Live exam interface |
| `/exam/submitted/:id` | Student | Submission confirmation |
| `/attempts/:attemptId/result` | Student/authorized | Result and analysis report |
| `/parent` | Parent | Parent dashboard with children and progress |
| `/parent/children/:studentId` | Parent | Child detail page |
| `/upgrade` | Parent | Payment/upgrade page |
| `/payment/success` | Parent | Payment success |
| `/payment/failed` | Parent | Payment failure |
| `/payment/history` | Parent | Payment history and subscription summary |
| `/profile` | Authenticated | Profile, avatar, language, password |
| `/admin` | Admin | Admin dashboard |
| `/admin/questions` | Admin | Question manager/import/editor |
| `/admin/publish` | Admin | Publish/unpublish exams |
| `/admin/publish/create` | Admin | Create a new test/event |
| `/admin/images` | Admin | Image upload/admin media |
| `/admin/stats` | Admin | Question statistics |
| `/admin/settings` | Admin | System settings |
| `/admin/subscriptions` | Admin | Parent subscriptions, free users, grants, payments |

## Roles

Roles are stored in `public.user_profiles.role`. Authorization must not trust user-editable Supabase `user_metadata`.

Supported role values:

- `student`
- `parent`
- `teacher`
- `exam_admin`
- `super_admin`

Role homes:

| Role | Home |
| --- | --- |
| `student` | `/dashboard` |
| `parent` | `/parent` |
| `exam_admin`, `super_admin` | `/admin` |

Example role update in Supabase SQL Editor:

```sql
UPDATE user_profiles
SET role = 'exam_admin'
WHERE id = '<user-uuid>';
```

Find user by email:

```sql
SELECT up.id, up.full_name, up.role, au.email
FROM user_profiles up
JOIN auth.users au ON au.id = up.id
WHERE au.email = 'admin@example.com';
```

## Parent And Child Model

Parents create child profiles from the parent dashboard. Children are represented through `child_profiles` and linked to the parent. The parent dashboard shows:

- Child switcher
- Child profile card
- Weak and strong topics
- Recent mistakes
- Progress chart
- Attempt history
- Full wrong-answer drawer for premium users

Current rule:

- A parent may create at most two active child profiles.

Premium access is per parent account. If the wrong email receives access, the logged-in parent will still see the free plan. The sidebar displays the logged-in email to make this easier to verify.

## Payments And Access Control

Payments use Razorpay and are owned by the `payment` module.

Key tables:

- `subscription_plans`
- `subscriptions`
- `payments`
- `app_settings`

Key endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/payment/plans` | Active public plan metadata |
| `GET` | `/api/payment/status` | Current parent subscription status |
| `POST` | `/api/payment/create-order` | Create Razorpay order and pending subscription |
| `POST` | `/api/payment/verify` | Verify payment signature and activate subscription |
| `POST` | `/api/payment/webhook` | Razorpay webhook handler |
| `GET` | `/api/payment/history` | Parent payment history |
| `GET` | `/api/admin/subscriptions` | Admin subscription/free-parent list |
| `POST` | `/api/admin/subscriptions/grant` | Admin manual premium grant |
| `POST` | `/api/admin/subscriptions/{id}/extend` | Extend subscription |
| `POST` | `/api/admin/subscriptions/{id}/cancel` | Cancel subscription |

Free tier behavior:

- Free parents can see limited access and upgrade prompts.
- Premium parents get full exam and analysis access based on `parent_has_active_subscription()` and backend access context checks.
- Admin subscription list includes both paid and free parent users.

## Question Security

Question delivery uses `v_exam_questions`, which excludes correct answers. Correct answers are exposed only through review/admin paths after authorization checks.

Important rules:

- Do not return `correct_option` or `correct_options` during active exam delivery.
- Use `v_exam_questions` for exam delivery.
- Use `v_exam_answers` only for post-submit review/analysis.
- Bulk import and question mutation endpoints require admin access.

Multi-select support:

- `questions.is_multi_select`
- `questions.correct_options`
- `responses.selected_options`
- Admin question edit UI supports multi-select.
- Attempt and analysis code must handle both `selected_option` and `selected_options`.

## Database And Migrations

Main SQL files:

| File | Purpose |
| --- | --- |
| `database/scholarpath_migration.sql` | Base schema, tables, views, triggers, seed data |
| `database/migration_adr013_014.sql` | Child profiles, subscriptions, payments, access control |
| `database/migration_multi_select.sql` | Multi-select question/response support |
| `database/migration_security_advisor_20260430.sql` | Supabase Security Advisor hardening |

Security hardening currently applied:

- App functions have fixed `search_path`.
- RLS enabled on exposed public tables.
- Missing RLS policies added.
- `v_exam_questions`, `v_exam_answers`, `v_student_attempts` set to `security_invoker=true`.
- `pg_trgm` moved from `public` to `extensions`.

Useful checks:

```sql
-- Tables with RLS disabled in public schema
SELECT c.relname AS table_name
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relkind = 'r'
  AND c.relrowsecurity = false
ORDER BY c.relname;

-- RLS-enabled tables without policies
SELECT c.relname AS table_name
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relkind = 'r'
  AND c.relrowsecurity = true
  AND NOT EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid = c.oid)
ORDER BY c.relname;

-- Views should be security_invoker
SELECT c.relname AS view_name, c.reloptions
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relkind IN ('v', 'm')
ORDER BY c.relname;
```

## Environment Variables

Backend variables are loaded by `backend/app/config.py` from `backend/.env` first and then `../.env`.

Minimum backend `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/postgres
SECRET_KEY=replace-with-at-least-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
SUPABASE_SERVICE_KEY=your-service-role-key

FRONTEND_URL=http://localhost:5173
DEBUG=true
APP_NAME=ScholarPath
APP_VERSION=1.0.0

MEDIA_PROVIDER=local
CLOUDINARY_URL=

RAZORPAY_KEY_ID=rzp_test_xxx
RAZORPAY_KEY_SECRET=xxx
RAZORPAY_WEBHOOK_SECRET=xxx
```

Optional R2 media variables:

```bash
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=scolarpath
R2_PUBLIC_URL=
```

Frontend `.env.local` in `frontend/`:

```bash
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_APP_NAME=ScholarPath
VITE_DEFAULT_LANGUAGE=en
VITE_RAZORPAY_KEY_ID=rzp_test_xxx
```

Never commit real `.env`, service-role keys, Razorpay secrets, or Supabase JWT secrets.

## Local Development

### Backend

From the project root:

```bash
cd backend
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cd ..
DEBUG=true PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Interactive API docs are available only when `DEBUG=true`:

- http://localhost:8000/docs
- http://localhost:8000/redoc

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Default URL:

- http://localhost:5173

If port 5173 is busy, Vite may use another port. Add that port to backend CORS if needed.

## Testing

Backend:

```bash
cd backend
. .venv/bin/activate
pytest -q
```

Focused examples:

```bash
cd backend
. .venv/bin/activate
pytest app/modules/payment/tests app/modules/user/tests/test_router.py -q
pytest app/modules/question/tests -q
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

Known local issue:

- If `frontend/dist` contains root-owned generated files, `npm run build` may fail while cleaning `dist`.
- Fix local permissions or build to a clean output directory:

```bash
cd frontend
npm run build -- --outDir dist-codex
```

## Deployment

### Backend: Google Cloud Run

From `backend/`:

```bash
gcloud run deploy scholarpath-backend \
  --source . \
  --region us-central1 \
  --project scholarpath-app \
  --allow-unauthenticated \
  --quiet
```

Describe active revision and URL:

```bash
gcloud run services describe scholarpath-backend \
  --region=us-central1 \
  --project=scholarpath-app \
  --format='value(status.latestReadyRevisionName,status.url)'
```

Smoke check:

```bash
curl -sS -o /dev/null -w 'backend:%{http_code}\n' \
  https://scholarpath-backend-470258820905.us-central1.run.app/api/catalog/boards
```

### Frontend: Firebase Hosting

Normal deploy from `frontend/`:

```bash
npm run build
firebase deploy --only hosting --project scholarpath-app
```

If local `dist` permissions are broken, use a temporary output and config:

```bash
npm run build -- --outDir dist-codex
# temporarily point Firebase hosting.public to dist-codex or use a temporary config
firebase deploy --only hosting --project scholarpath-app --config firebase.codex.json
```

Smoke check:

```bash
curl -sS -o /dev/null -w 'frontend:%{http_code}\n' https://scholarpath-app.web.app
```

## Exam Data And Import Tooling

The **current** way to import a paper is the review-first PDF importer — see
[`UploadQuestionPDF.md`](UploadQuestionPDF.md) and `backend/app/modules/question/pdf_importer.py`
(admin endpoint `POST /api/admin/questions/pdf-import`).

For programmatic JSON import there is the admin bulk-import endpoint:

```text
POST /api/admin/questions/bulk-import
```

This endpoint is admin-protected and replaces an exam's question set through backend
validation. See [`template.json`](template.json) for the payload format.

### Historical helpers (`archive/`)

The one-off extraction/render/import scripts and extracted-data JSON that were used to seed
the 2017–2025 MSCE papers and 8th-standard 2025 content now live under `archive/` (see
`archive/README.md`). They are superseded by the PDF importer, unmaintained, and not wired
into the app. The large rendered page scans are kept locally under `archive/rendered/` and
are git-ignored.

## Useful SQL Queries

Users and roles:

```sql
SELECT up.id, up.full_name, up.role, up.is_onboarded, au.email
FROM user_profiles up
JOIN auth.users au ON au.id = up.id
ORDER BY up.created_at DESC;
```

Parent subscriptions:

```sql
SELECT up.id, up.full_name, au.email,
       s.status, s.started_at, s.expires_at,
       parent_has_active_subscription(up.id) AS has_active_subscription
FROM user_profiles up
JOIN auth.users au ON au.id = up.id
LEFT JOIN LATERAL (
    SELECT *
    FROM subscriptions s
    WHERE s.parent_id = up.id
    ORDER BY s.created_at DESC
    LIMIT 1
) s ON true
WHERE up.role = 'parent'
ORDER BY up.created_at DESC;
```

Question counts per exam:

```sql
SELECT e.id, e.paper_code, e.title_en, e.is_active,
       COUNT(q.id) AS loaded,
       e.total_questions AS required
FROM exams e
LEFT JOIN questions q ON q.exam_id = e.id
GROUP BY e.id
ORDER BY e.id;
```

Attempts:

```sql
SELECT a.id, a.child_profile_id, e.title_en, a.status,
       a.total_score, a.percentage, a.grade, a.submitted_at
FROM attempts a
JOIN exams e ON e.id = a.exam_id
ORDER BY a.started_at DESC;
```

Parent-child links:

```sql
SELECT p.full_name AS parent_name,
       c.full_name AS child_name,
       c.std_class,
       c.medium,
       c.is_active
FROM child_profiles c
JOIN user_profiles p ON p.id = c.parent_id
ORDER BY p.full_name, c.created_at;
```

## Operational Notes

- Supabase Auth creates users; `handle_new_auth_user()` creates the matching `user_profiles` row.
- Backend role checks load trusted roles from `user_profiles`, not JWT `user_metadata`.
- Parent premium grants are tied to exact auth email/user id.
- Parent dashboard refreshes subscription status on page load, focus, and visibility changes.
- Free-tier wrong-answer summaries are cleared when premium status becomes active so full details are refetched.
- Cloud Run and Firebase deployments should be smoke-tested after every deploy.
- Direct DB changes should be mirrored in a SQL migration file under `database/`.

## Git Notes

Recent important commits:

- `3956de0 Fix subscription visibility and Supabase security`
- `e503b32 Add exam import data and tooling`

If Git object permissions are broken locally:

```bash
sudo chown -R "$(id -un):$(id -gn)" .git/objects
chmod -R u+rwX .git/objects
find .git/objects -maxdepth 2 \( ! -user "$(id -un)" -o ! -perm -u+w \) -print | head
```

The final verification command should print nothing.

## Production Readiness Checklist

Before treating a release as production-ready, verify:

- Backend tests pass: `pytest -q`
- Frontend tests pass: `npm test`
- Frontend production build passes: `npm run build`
- Cloud Run health/API smoke checks return `200`
- Firebase Hosting smoke check returns `200`
- Supabase Security Advisor has no unresolved critical issues
- RLS and view security checks still pass after migrations
- Razorpay test/live keys match the target environment
- `FRONTEND_URL` matches the deployed Firebase URL
- No secrets are committed
- Admin role is assigned only to trusted accounts
- Parent premium grants use the correct login email

## ADRs

Architecture Decision Records are in `docs/adr/`:

- ADR-001 Authentication Strategy
- ADR-002 Vertical Slice Architecture
- ADR-003 Multilingual Data Design
- ADR-004 Question Content Model
- ADR-005 Exam Attempt State Machine
- ADR-006 Score Computation Strategy
- ADR-007 Media Storage Provider Pattern
- ADR-008 Database Platform Selection
- ADR-009 Parent-Student Authorization Model
- ADR-010 Frontend Module Communication
- ADR-011 Exam Scalability Model
- ADR-012 Question Answer Security
- ADR-013 Child Profile Model
- ADR-014 Payment and Access Control
