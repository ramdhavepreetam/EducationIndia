# ScholarPath — Project Knowledge File
# Read this file first before making any code changes.
# Updated: 2026-02-23 | Version: 1.3.0

---

## What This Project Is

ScholarPath is a multilingual online exam preparation portal for Indian students
taking Maharashtra MSCE Scholarship Examinations (5th and 8th standard).

Target users: Students (age 10-14), Parents, Exam Admins
Languages: English + Marathi (Hindi-ready architecture, add later via ALTER TABLE)
Scale goal: Start with 1 exam, grow to multiple boards and exam types

---

## Tech Stack

```
Backend:   Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic
Database:  PostgreSQL via Supabase (free tier to start)
Auth:      Supabase Auth (Google + Facebook OAuth + Email/Password)
Frontend:  React 18 + Vite + Tailwind CSS 3 + Zustand + react-i18next
HTTP:      Axios with request/response interceptors
Charts:    Recharts
PDF:       jsPDF + html2canvas (exam result report cards)
Deploy:    Vercel (frontend) + Render (backend) + Supabase (DB + Auth)
Media:     Local filesystem (dev) → Cloudinary (prod) via provider pattern
```

---

## Module Map (Vertical Slice Architecture)

```
/backend/app/modules/
├── auth/         → JWT + Supabase session bridge, role verification
├── user/         → Student + parent profiles, parent-child linking
├── catalog/      → Exam boards, events, papers, sections, topics
├── question/     → Question bank, options, contexts, bulk import
├── attempt/      → Exam session lifecycle (start → autosave → submit)
├── analysis/     → Scoring engine, topic performance, recommendations
├── media/        → File upload, image serving (provider pattern)
└── admin/        → Orchestrator only, zero business logic

/frontend/src/modules/
├── auth/         → Login, register, OAuth callback
├── exam/         → Exam listing, exam details
├── attempt/      → Exam-taking interface (timer, palette, autosave)
├── analysis/     → Result page, report card, PDF export
├── dashboard/    → Student home, progress overview
├── parent/       → Parent dashboard, child monitoring
└── admin/        → Admin panel, question management
```

---

## Module Boundaries — NEVER Cross These

```
auth      → Owns: auth columns in users table
            Exposes: verify_token(), require_role()
            Consumes: Nothing (no module dependencies)

user      → Owns: user_profiles, parent_student_links
            Exposes: UserService.get_profile(), UserService.update_profile()
            Consumes: Auth (verify_token dependency only)

catalog   → Owns: exam_boards, exam_categories, exam_events, exams, sections, topics
            Exposes: CatalogService.get_exam(), CatalogService.list_exams()
            Consumes: Auth (admin role check only)

question  → Owns: questions, options, question_contexts
            Exposes: QuestionService.get_questions_for_exam(), validate_answer()
            Consumes: Catalog (exam_id validation), Media (image_url)
            RULE: NEVER return correct_option during active exam delivery

attempt   → Owns: attempts, responses
            Exposes: AttemptService.start(), save_response(), submit()
            Consumes: Catalog, Question, Auth
            RULE: Does NOT calculate scores. Raw response storage only.

analysis  → Owns: NO tables (read-only access to attempts + questions)
            Exposes: AnalysisService.generate_report(), get_user_performance()
            Consumes: Attempt (read-only), Question (correct answers + topics)
            RULE: Pure computation. No side effects. No DB writes.

media     → Owns: media_files table
            Exposes: MediaService.upload(), MediaService.delete()
            Consumes: Auth (upload permissions)
            RULE: Swap providers via MEDIA_PROVIDER env var only

admin     → Owns: NO tables
            Exposes: /api/admin/* routes
            Consumes: All modules via public interfaces only
            RULE: Zero business logic. Aggregate and delegate only.
```

---

## Database — Key Rules

```
Multilingual pattern:   column_en TEXT, column_mr TEXT
                        To add Hindi: ALTER TABLE x ADD COLUMN column_hi TEXT
                        Nothing else changes.

correct_option:         NEVER sent to frontend during active exam.
                        Use v_exam_questions view (excludes correct_option).
                        Use v_exam_answers view for post-exam review only.

Score computation:      Computed ONCE on submit.
                        Stored as JSONB in attempts.section_scores,
                        attempts.topic_scores, attempts.time_analysis.
                        Never recomputed on every read.

question_stats:         Updated by DB trigger on attempt submission.
                        Never updated in application code.

RLS pattern:
  Students → own data only
  Parents  → linked children's data via parent_student_links
  Admins   → bypass via is_admin() helper
  Public   → active exams + questions (read only)
```

---

## Database Schema — Full Reference

Full migration SQL: /database/scholarpath_migration.sql
Run once in Supabase SQL Editor. Never hand-edit production tables.
When writing SQLAlchemy models, column names MUST match this schema exactly.

### ENUMS (PostgreSQL types — use these exact string values)

```
user_role:        student | parent | teacher | exam_admin | super_admin
medium_type:      english | marathi | hindi | semi_english
question_type:    text | text_image | image_only | context_text |
                  context_image | marathi_only | bilingual
attempt_status:   ongoing | submitted | expired | abandoned
assignment_type:  practice | assigned | mock_test
context_type:     paragraph | poem | advertisement | image | pictograph |
                  instruction | venn_diagram | figure_series | table | data_chart
difficulty_level: easy | medium | hard
enquiry_status:   new | contacted | resolved | spam
```

### TABLE: exam_boards
```
id            SERIAL PK
name_en       TEXT NOT NULL
name_mr       TEXT
short_code    VARCHAR(20) UNIQUE NOT NULL    -- 'MSCE', 'CBSE'
state         TEXT
website_url   TEXT
logo_url      TEXT
is_active     BOOLEAN DEFAULT true
created_at    TIMESTAMPTZ
```

### TABLE: exam_categories
```
id              SERIAL PK
board_id        INT FK → exam_boards.id
name_en         TEXT NOT NULL
name_mr         TEXT
description_en  TEXT
description_mr  TEXT
icon_url        TEXT
is_active       BOOLEAN DEFAULT true
created_at      TIMESTAMPTZ
```

### TABLE: exam_events
```
id                    SERIAL PK
board_id              INT FK → exam_boards.id
category_id           INT FK → exam_categories.id
title_en              TEXT NOT NULL
title_mr              TEXT
std_class             SMALLINT NOT NULL        -- 5 or 8
year                  SMALLINT NOT NULL
exam_date             DATE
registration_deadline DATE
description_en        TEXT
description_mr        TEXT
is_active             BOOLEAN DEFAULT false
created_at            TIMESTAMPTZ
```

### TABLE: exams
```
id                   SERIAL PK
event_id             INT FK → exam_events.id
paper_code           VARCHAR(10) NOT NULL     -- '501', '502'
set_code             VARCHAR(5) DEFAULT 'A'
paper_number         SMALLINT
title_en             TEXT NOT NULL
title_mr             TEXT
medium               medium_type DEFAULT 'english'
total_questions      SMALLINT DEFAULT 75
total_marks          SMALLINT DEFAULT 150
marks_per_question   SMALLINT DEFAULT 2
duration_minutes     SMALLINT DEFAULT 90
instructions_en      TEXT
instructions_mr      TEXT
is_active            BOOLEAN DEFAULT false
created_at           TIMESTAMPTZ
UNIQUE(paper_code, set_code)
```

### TABLE: sections
```
id             SERIAL PK
exam_id        INT FK → exams.id
section_label  VARCHAR(5) NOT NULL     -- 'I', 'II'
subject_en     TEXT NOT NULL           -- 'English', 'Mathematics'
subject_mr     TEXT
question_from  SMALLINT NOT NULL       -- 1
question_to    SMALLINT NOT NULL       -- 25
order_index    SMALLINT DEFAULT 1
color_hex      VARCHAR(7) DEFAULT '#3B82F6'
```

### TABLE: topics
```
id              SERIAL PK
section_id      INT FK → sections.id
name_en         TEXT NOT NULL
name_mr         TEXT
description_en  TEXT
description_mr  TEXT
order_index     SMALLINT DEFAULT 1
```

### TABLE: question_contexts
```
id               SERIAL PK
exam_id          INT FK → exams.id
context_type     context_type NOT NULL
title_en         TEXT
title_mr         TEXT
content_en       TEXT                  -- passage / poem text
content_mr       TEXT
image_url        TEXT
image_alt_en     TEXT
image_alt_mr     TEXT
instruction_en   TEXT                  -- "Q27-28: Select mirror image..."
instruction_mr   TEXT
applies_from     SMALLINT              -- Q no. from
applies_to       SMALLINT              -- Q no. to
order_index      SMALLINT
created_at       TIMESTAMPTZ
```

### TABLE: questions  ← MOST IMPORTANT TABLE
```
id                        SERIAL PK
exam_id                   INT FK → exams.id
section_id                INT FK → sections.id
topic_id                  INT FK → topics.id
context_id                INT FK → question_contexts.id  (NULL = standalone)
question_no               SMALLINT NOT NULL
question_type             question_type NOT NULL DEFAULT 'text'
text_en                   TEXT          -- NULL for image_only or marathi_only
text_mr                   TEXT          -- NULL for english-only questions
question_image_url        TEXT
question_image_alt_en     TEXT
question_image_alt_mr     TEXT
correct_option            SMALLINT NOT NULL  CHECK (1-4)
explanation_en            TEXT          -- shown after exam
explanation_mr            TEXT
hint_en                   TEXT          -- practice mode only
hint_mr                   TEXT
marks                     SMALLINT DEFAULT 2
difficulty                difficulty_level DEFAULT 'medium'
tags                      TEXT[] DEFAULT '{}'
attempt_count             INT DEFAULT 0
correct_count             INT DEFAULT 0
actual_difficulty_ratio   NUMERIC(4,3)
created_at                TIMESTAMPTZ
updated_at                TIMESTAMPTZ
UNIQUE(exam_id, question_no)
```

### TABLE: options
```
id           SERIAL PK
question_id  INT FK → questions.id
option_no    SMALLINT NOT NULL  CHECK (1-4)
text_en      TEXT              -- NULL for image-only options
text_mr      TEXT
image_url    TEXT              -- NULL for text-only options
image_alt_en TEXT
image_alt_mr TEXT
is_correct   BOOLEAN DEFAULT false   -- synced by trigger from questions.correct_option
UNIQUE(question_id, option_no)
```

### TABLE: user_profiles  ← extends auth.users
```
id                  UUID PK FK → auth.users(id)
full_name           TEXT NOT NULL
role                user_role DEFAULT 'student'
avatar_url          TEXT
phone               TEXT
preferred_language  VARCHAR(5) DEFAULT 'en'   -- 'en', 'mr', 'hi'
std_class           SMALLINT                  -- 5 or 8 (students only)
medium              medium_type
school_name         TEXT
district            TEXT
state               TEXT DEFAULT 'Maharashtra'
date_of_birth       DATE
auth_provider       TEXT DEFAULT 'email'      -- 'email', 'google', 'facebook'
is_active           BOOLEAN DEFAULT true
is_onboarded        BOOLEAN DEFAULT false
subscription_tier   VARCHAR(20) DEFAULT 'free'
subscription_expiry TIMESTAMPTZ
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

### TABLE: parent_student_links
```
id              SERIAL PK
parent_id       UUID FK → user_profiles.id
student_id      UUID FK → user_profiles.id
child_nickname  TEXT
linked_by       UUID FK → user_profiles.id
linked_at       TIMESTAMPTZ
is_active       BOOLEAN DEFAULT true
UNIQUE(parent_id, student_id)
CHECK(parent_id != student_id)
```

### TABLE: exam_assignments
```
id               SERIAL PK
exam_id          INT FK → exams.id
student_id       UUID FK → user_profiles.id
assigned_by      UUID FK → user_profiles.id   (NULL = self-practice)
assignment_type  assignment_type DEFAULT 'practice'
max_attempts     SMALLINT DEFAULT 10
attempts_used    SMALLINT DEFAULT 0
valid_from       TIMESTAMPTZ
valid_until      TIMESTAMPTZ
is_active        BOOLEAN DEFAULT true
created_at       TIMESTAMPTZ
UNIQUE(exam_id, student_id)
```

### TABLE: attempts
```
id                UUID PK DEFAULT gen_random_uuid()
student_id        UUID FK → user_profiles.id
exam_id           INT FK → exams.id
assignment_id     INT FK → exam_assignments.id
attempt_number    SMALLINT DEFAULT 1
status            attempt_status DEFAULT 'ongoing'
started_at        TIMESTAMPTZ
submitted_at      TIMESTAMPTZ
last_saved_at     TIMESTAMPTZ
duration_seconds  INT
total_score       SMALLINT
total_correct     SMALLINT
total_wrong       SMALLINT
total_skipped     SMALLINT
percentage        NUMERIC(5,2)
grade             VARCHAR(20)       -- 'Excellent','Good','Average','Below Average'
section_scores    JSONB DEFAULT '[]'
  -- [{"section_id":1,"label":"I","subject":"English","score":38,"total":50,"percentage":76.0}]
topic_scores      JSONB DEFAULT '[]'
  -- [{"topic_id":3,"name":"Grammar","correct":4,"total":5,"percentage":80,"status":"strong"}]
time_analysis     JSONB DEFAULT '{}'
  -- {"avg_per_question":72,"fastest":{"q_no":3,"seconds":15},"slowest":{"q_no":47,"seconds":220}}
recommendations   JSONB DEFAULT '[]'
  -- ["Practice more Fractions — scored 40%"]
ip_address        INET
user_agent        TEXT
created_at        TIMESTAMPTZ
```

### TABLE: responses
```
id                  BIGSERIAL PK
attempt_id          UUID FK → attempts.id
question_id         INT FK → questions.id
question_no         SMALLINT NOT NULL      -- denormalized for fast sort
selected_option     SMALLINT  CHECK (1-4, NULL = skipped)
is_correct          BOOLEAN               -- NULL until submitted
marks_obtained      SMALLINT DEFAULT 0
first_visited_at    TIMESTAMPTZ
answered_at         TIMESTAMPTZ
time_taken_seconds  SMALLINT
visit_count         SMALLINT DEFAULT 0    -- drives palette color
is_marked_review    BOOLEAN DEFAULT false -- orange flag in palette
UNIQUE(attempt_id, question_id)
```

### TABLE: question_stats
```
question_id          INT PK FK → questions.id
total_attempts       INT DEFAULT 0
correct_count        INT DEFAULT 0
wrong_count          INT DEFAULT 0
skip_count           INT DEFAULT 0
avg_time_seconds     NUMERIC(6,2) DEFAULT 0
actual_difficulty    NUMERIC(4,3) DEFAULT 0   -- 0.0=easy, 1.0=very hard
updated_at           TIMESTAMPTZ
-- Updated by DB trigger on attempt submission. Never write from app code.
```

### TABLE: exam_stats
```
exam_id         INT PK FK → exams.id
total_attempts  INT DEFAULT 0
avg_score       NUMERIC(5,2)
avg_percentage  NUMERIC(5,2)
highest_score   SMALLINT
pass_count      INT
updated_at      TIMESTAMPTZ
```

### TABLE: notifications
```
id          BIGSERIAL PK
user_id     UUID FK → user_profiles.id
type        VARCHAR(50)     -- 'exam_assigned','result_ready','exam_reminder'
title_en    TEXT NOT NULL
title_mr    TEXT
body_en     TEXT
body_mr     TEXT
data        JSONB DEFAULT '{}'
is_read     BOOLEAN DEFAULT false
read_at     TIMESTAMPTZ
created_at  TIMESTAMPTZ
```

### TABLE: enquiries
```
id            SERIAL PK
name          TEXT NOT NULL
email         TEXT
phone         TEXT
school_name   TEXT
district      TEXT
std_class     SMALLINT
message       TEXT
status        enquiry_status DEFAULT 'new'
admin_notes   TEXT
responded_by  UUID FK → user_profiles.id
responded_at  TIMESTAMPTZ
source        TEXT DEFAULT 'website'
referral_code TEXT
created_at    TIMESTAMPTZ
```

### VIEWS — Always use these, never raw tables for these purposes
```
v_exam_questions    → Safe exam delivery. Joins questions + sections + topics +
                      question_contexts. EXCLUDES correct_option and explanation.
                      Use for: GET /api/questions during active exam

v_exam_answers      → Full data including correct_option + explanation_en/mr.
                      Use for: POST-exam review page only (after attempt submitted)

v_student_attempts  → Joins attempts + exams + exam_events.
                      Use for: Student dashboard, parent dashboard
```

### TRIGGERS (automatic — never replicate in app code)
```
questions_updated_at          → sets questions.updated_at on every UPDATE
user_profiles_updated_at      → sets user_profiles.updated_at on every UPDATE
sync_correct_option_trigger   → syncs options.is_correct when questions.correct_option changes
update_question_stats_trigger → updates question_stats when attempt.status → 'submitted'
increment_attempts_used       → increments exam_assignments.attempts_used on submit
on_auth_user_created          → creates user_profiles row on every Supabase Auth signup
```

### RLS HELPER FUNCTIONS (already in DB — use in service layer checks)
```sql
is_admin()                           -- true if current user is exam_admin or super_admin
is_parent()                          -- true if current user role = 'parent'
parent_can_see_student(student_id)   -- true if parent_student_links row exists + is_active
```

### INDEXES (already created — use these columns in WHERE clauses)
```
questions:    (exam_id), (exam_id, question_no), (section_id), (topic_id)
responses:    (attempt_id), (question_id)
attempts:     (student_id), (exam_id), (student_id, exam_id), (status), (submitted_at DESC)
assignments:  (student_id), (exam_id)
links:        (parent_id), (student_id)
notifications:(user_id), (user_id, is_read) WHERE is_read = false
```

### SEEDED DATA (already in DB after running migration)
```
exam_boards:      1 row  → MSCE Maharashtra
exam_categories:  1 row  → Pre-Upper Primary Scholarship
exam_events:      1 row  → MSCE 5th Std 2025
exams:            2 rows → Paper 501 (Paper I) + Paper 502 (Paper II)
sections:         4 rows → I+II for each paper
topics:          26 rows → Grammar, Fractions, Mirror Images, etc.
exam_stats:       2 rows → initialized for both exams
```

---

## Exam Structure (from actual MSCE papers)

```
Paper 0501 (Paper I):
  Section I  Q1-25  → First Language (English)
  Section II Q26-75 → Mathematics
  75 questions × 2 marks = 150 marks | 90 minutes

Paper 0502 (Paper II):
  Section I  Q1-25  → Third Language (Marathi — no English version)
  Section II Q26-75 → Intelligence Test
  75 questions × 2 marks = 150 marks | 90 minutes

Question Types:
  text          → Pure text question + text options (most common)
  text_image    → Text question + image in question body
  image_only    → Image IS the question (Intelligence Test figures)
  context_text  → Belongs to passage/poem context
  context_image → Belongs to pictograph/figure context
  marathi_only  → No English version exists (Marathi section)
  bilingual     → Shown simultaneously EN + MR side by side

Contexts (shared by multiple questions):
  paragraph, poem, advertisement, image, pictograph,
  instruction, venn_diagram, figure_series, table, data_chart
```

---

## Frontend Module Rules

```
Each module exports ONLY through its index.js:
  // Good:  import { ExamPage } from '@/modules/attempt'
  // Bad:   import ExamShell from '@/modules/attempt/components/ExamShell'

State management:
  authStore    → { user, token, login(), logout() }
  attemptStore → { currentAttempt, responses, saveResponse(), timer, questionStatus }
  analysisStore→ { report, loading, fetchReport() }

API client (config/apiClient.js):
  Base URL from VITE_API_URL env var
  Request interceptor: attach JWT token
  Response interceptor: handle 401 → auto logout, network errors globally

Language:
  Default from user_profiles.preferred_language
  Persisted to localStorage
  Applied via react-i18next useTranslation() hook
  Question text served in user's preferred language from API
```

---

## ADR Index — Architecture Decisions

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Authentication Strategy | Accepted |
| ADR-002 | Vertical Slice Architecture | Accepted |
| ADR-003 | Multilingual Data Design | Accepted |
| ADR-004 | Question Content Model | Accepted |
| ADR-005 | Exam Attempt State Machine | Accepted |
| ADR-006 | Score Computation Strategy | Accepted |
| ADR-007 | Media Storage Provider Pattern | Accepted |
| ADR-008 | Database Platform Selection | Accepted |
| ADR-009 | Parent-Student Authorization Model | Accepted |
| ADR-010 | Frontend Module Communication | Accepted |
| ADR-011 | Exam Scalability Model | Accepted |
| ADR-012 | Question Answer Security | Accepted |

All ADRs located at: /docs/adr/

---

## What AI Should NOT Do in This Project

```
NEVER add business logic to admin module
NEVER query correct_option in exam delivery endpoints
NEVER compute scores inside attempt module
NEVER import module internals across module boundaries
  → Wrong: from app.modules.auth.models import User
  → Right: from app.modules.auth.dependencies import verify_token

NEVER put DB queries in routers — routers call services only
NEVER put DB queries in services — use repository pattern in repository.py
NEVER write scores into attempts from analysis module
NEVER let attempt module read question.correct_option directly
NEVER change multilingual column names (breaking change to API contracts)
```

---

## Environment Variables Required

```bash
# Backend
DATABASE_URL=postgresql://user:pass@host/scholarpath
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
MEDIA_PROVIDER=local                    # or cloudinary
CLOUDINARY_URL=cloudinary://...         # only if provider=cloudinary
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# Frontend
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_APP_NAME=ScholarPath
VITE_DEFAULT_LANGUAGE=en
```

---

## How to Add a New Exam (Scaling Pattern)

```
1. Insert into exam_boards if new board (CBSE, SSC, etc.)
2. Insert into exam_categories if new category
3. Insert into exam_events for the new year/edition
4. Insert into exams for each paper
5. Insert into sections for each paper's sections
6. Insert into topics for analysis categories
7. Bulk import questions via POST /api/admin/questions/bulk-import
8. Set exams.is_active = true when ready to publish
No code changes required. Pure data operation.
```

---

## When to Write a New ADR

Write a new ADR when you are about to:
- Choose between two real technical options that affect multiple modules
- Make a decision that will be hard to reverse later
- Cross or redefine a module boundary
- Change how multilingual content is stored or served
- Add a new external service or dependency
- Define a new data ownership rule

Template: /docs/adr/ADR-TEMPLATE.md

---

## Build Progress

Last updated: 2026-02-23

### Infrastructure (complete)
```
backend/app/main.py              ✅ FastAPI app, CORS (ports 5173+5174), lifespan,
                                    exception handlers, JWKS fetch on startup
backend/pytest.ini               ✅ asyncio_mode=auto (fixes all async test discovery)
backend/app/config.py            ✅ pydantic-settings v2, reads .env from project root
backend/app/database.py          ✅ async SQLAlchemy engine, get_db() dependency
backend/app/shared/exceptions.py ✅ BadRequest, Unauthorized, Forbidden, NotFound, Conflict
backend/app/shared/i18n.py       ✅ get_language(request), pick(obj, field, lang)
backend/requirements.txt         ✅ FastAPI, SQLAlchemy 2.0, asyncpg, jose, pydantic v2
backend/.venv/                   ✅ Python venv at backend/.venv
.env                             ✅ DATABASE_URL + SUPABASE_URL + SUPABASE_JWT_SECRET set
.env.local                       ✅ Frontend Supabase keys set (VITE_SUPABASE_URL + ANON_KEY)
database/scholarpath_migration.sql ✅ Applied to Supabase — all 18 tables, RLS, triggers, views
```

Run backend:
```
DEBUG=true PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Backend Modules
```
modules/auth/      ✅ COMPLETE
  dependencies.py  → verify_token() supports ES256 (JWKS) + HS256 (legacy)
                     require_role(), require_student, require_parent,
                     require_admin, require_super_admin
                     set_jwks_keys() — called by main.py lifespan on startup
  (no router — Supabase handles login/register)

modules/user/      ✅ COMPLETE
  models.py        → UserProfile, ParentStudentLink
  schemas.py       → UserProfileResponse, ChildProfileResponse, UpdateProfileRequest,
                     CompleteProfileRequest, LinkChildRequest
  repository.py    → get_by_id, get_user_id_by_email (cross-schema auth.users),
                     update, get_children_with_links, get/create/update_link
  service.py       → get_my_profile, update_my_profile, complete_profile, link_child
  router.py        → GET /me, PUT /me, POST /me/complete-profile,
                     GET /my-children, POST /link-child
  tests/           → test_service.py (unit, mocked repo), test_router.py (integration)

modules/catalog/   ✅ COMPLETE
  models.py        → ExamBoard, ExamCategory, ExamEvent, Exam, Section, Topic
  schemas.py       → BoardResponse, ExamSummaryResponse, ExamDetailResponse
                     (nested sections+topics), PublishExamResponse
  repository.py    → list_active_boards, list_exams (filtered), get_exam_by_id
                     (selectinload sections→topics), set_exam_active
  service.py       → list_boards, list_exams, get_exam, get_active_exam,
                     publish_exam, unpublish_exam
  router.py        → GET /boards, GET /exams, GET /exams/{id}, PUT /exams/{id}/publish
  tests/           → test_service.py (11 unit tests, 5 test classes)
  README.md        ✅

modules/question/  ✅ COMPLETE
  models.py        → QuestionContext, Question, Option (enums: QuestionTypeEnum,
                     DifficultyLevelEnum, ContextTypeEnum; create_type=False)
  schemas.py       → QuestionDeliverySchema (security boundary — no correct_option),
                     QuestionReviewSchema (+correct_option, post-submit only),
                     QuestionAdminSchema (full data), BulkImportSchema (ADR-004 format)
  repository.py    → fetch_by_exam_id (v_exam_questions view via text()),
                     fetch_by_id_for_review/admin (Question ORM + selectinload),
                     get_attempt_status (cross-module text() — temp until attempt module),
                     bulk_insert (contexts → questions → options with ctx_ref resolution)
  service.py       → get_questions_for_exam (validates active exam + calls repo),
                     get_question_for_review (validates attempt owner + submitted status),
                     bulk_import (full validation pipeline), update_question, delete_question
  router.py        → router (GET /api/questions/, GET /api/questions/{id}/review),
                     admin_router (GET/PUT/DELETE /api/admin/questions/, POST bulk-import)
  importer.py      → validate_question_import() — 7 type-specific validators + 4 option validators
  tests/           → test_service.py (9 tests), test_importer.py (21 tests),
                     test_security.py (10 tests including schema field allowlist)
  README.md        ✅

modules/attempt/   ⬜ NOT STARTED
modules/analysis/  ⬜ NOT STARTED
modules/media/     ⬜ NOT STARTED
modules/admin/     ⬜ NOT STARTED
```

### Frontend Modules
```
frontend/package.json            ✅ React 18, Vite, Zustand, axios, supabase-js, i18next
frontend/vite.config.js          ✅ @/ alias → ./src
frontend/src/main.jsx            ✅ BrowserRouter with v7_startTransition + v7_relativeSplatPath
frontend/src/App.jsx             ✅ Routes + AuthRedirect (handles OAuth callback at /)
frontend/src/config/
  supabaseClient.js              ✅ createClient with env var validation
  apiClient.js                   ✅ Axios + JWT interceptor + 401 auto-logout
  i18n.js                        ✅ react-i18next setup

modules/auth/                    ✅ COMPLETE
  api/authApi.js                 ✅ getMe(), completeProfile()
  store/authStore.js             ✅ Zustand: initialize(), login(), loginWithGoogle(),
                                    loginWithFacebook(), register(), logout(), setLanguage()
  pages/LoginPage.jsx            ✅ Email/password + Google + Facebook + redirect if authed
  pages/RegisterPage.jsx         ✅ Email/password registration
  pages/OnboardingPage.jsx       ✅ Profile completion form (sets is_onboarded=true)
  components/ProtectedRoute.jsx  ✅ Redirects unauthenticated users to /login
  index.js                       ✅ Barrel export for all auth pages + store + ProtectedRoute

shared/layouts/
  AuthLayout.jsx                 ✅ Centered card layout for auth + onboarding pages
  AppLayout.jsx                  ✅ Sidebar + header layout for authenticated app

modules/exam/      ⬜ NOT STARTED
modules/attempt/   ⬜ NOT STARTED
modules/analysis/  ⬜ NOT STARTED
modules/dashboard/ ⬜ NOT STARTED (placeholder in App.jsx)
modules/parent/    ⬜ NOT STARTED
modules/admin/     ⬜ NOT STARTED
```

### Pending Tasks
```
TODO: Seed 150 MSCE exam questions via bulk-import endpoint
      → Prepare JSON in BulkImportSchema format for Paper 501 + Paper 502
      → POST /api/admin/questions/bulk-import with admin JWT
      → Run GET /api/questions/?exam_id=1 to verify (should return 75 items, no correct_option)

TODO: Scaffold attempt module (Day 7 — state machine + autosave + submit)
      → Models: attempts, responses
      → State machine: not_started → ongoing → submitted | expired | abandoned
      → Per-answer upsert via responses table
      → Server-side timer (started_at + duration_minutes)
      → Submit scores are computed by ANALYSIS module, not attempt module

TODO: Scaffold analysis module (Day 9 — scorer.py + recommender.py)
      → Pure functions only, no DB writes
      → Called by attempt module on submit

TODO: Scaffold frontend exam module (exam listing + exam detail pages)
TODO: Scaffold frontend attempt module (timer + palette + question cards + autosave)
TODO: Scaffold frontend analysis module (result page + PDF report card)
TODO: Scaffold media, admin backend modules

TODO: Enable Facebook OAuth in Supabase dashboard
      → Authentication → Providers → Facebook (add App ID + Secret)
      → Google OAuth is already enabled and working

TODO: Complete OnboardingPage form logic
      → Currently scaffolded; needs to call completeProfile() and set is_onboarded=true
      → Then redirect to /dashboard
```

---

## Established Implementation Patterns

These patterns are locked in across all existing modules — follow them exactly.

### Repository singleton
```python
# Every module/repository.py ends with:
catalog_repository = CatalogRepository()

# Every module/service.py ends with:
catalog_service = CatalogService()

# Service imports the singleton, not the class:
from app.modules.catalog.repository import catalog_repository
```

### Auth dependency aliases (auth/dependencies.py)
```python
require_student     = require_role("student")
require_parent      = require_role("parent")
require_admin       = require_role("exam_admin", "super_admin")
require_super_admin = require_role("super_admin")

# Usage in router:
_: UserIdentity = Depends(require_admin)   # admin-only endpoint
identity: UserIdentity = Depends(verify_token)  # any authenticated user
```

### Supabase JWT structure
```
payload["sub"]                      → user UUID (string, cast to UUID)
payload["user_metadata"]["role"]    → app role (student/parent/etc.)
payload["aud"]                      → "authenticated" (required for decode)
payload["email"]                    → user email
```

### Cross-schema query (auth.users is Supabase-managed)
```python
# SQLAlchemy ORM cannot map auth.users — use text() for cross-schema queries
result = await db.execute(
    text("SELECT id FROM auth.users WHERE email = :email"),
    {"email": email.lower().strip()},
)
```

### get_active_exam() vs get_exam()
```python
catalog_service.get_exam(db, id)         # raises 404 if not found (any status)
catalog_service.get_active_exam(db, id)  # raises 404 if not found OR inactive
# attempt module must call get_active_exam() to prevent starting deactivated exams
```

### Partial update pattern
```python
# Always use exclude_unset=True (not exclude_none) for PATCH-style updates
# Distinguishes "field not provided" from "field explicitly set to null"
updates = data.model_dump(exclude_unset=True)
await user_repository.update(db, user_id, updates)
```

### Supabase JWT algorithm — ES256 (IMPORTANT)
```
New Supabase projects sign user session tokens with ES256 (elliptic curve), NOT HS256.
  - Token header: {"alg": "ES256", "kid": "...", "typ": "JWT"}
  - Public key fetched from: {SUPABASE_URL}/auth/v1/.well-known/jwks.json
  - Keys cached at startup via set_jwks_keys() in auth/dependencies.py
  - verify_token() detects alg from header → uses JWKS for ES256, JWT secret for HS256
  - SUPABASE_JWT_SECRET is still needed for legacy/service tokens (HS256)
  - Never put inline comments on the same line as SUPABASE_JWT_SECRET in .env
    (the # character and everything after it becomes part of the value)
```

### OAuth callback routing (React)
```
After Google OAuth, Supabase redirects to the app root ("/").
App.jsx must have routes for both index and catch-all that redirect based on auth state:
  <Route index element={<AuthRedirect />} />
  <Route path="*" element={<AuthRedirect />} />

AuthRedirect checks isAuthenticated + is_onboarded and navigates accordingly.
LoginPage must also redirect away if already authenticated (handles browser back button).
```

### Dual-router pattern (modules with admin endpoints)
```python
# Modules that have both student-facing + admin endpoints use TWO routers:
router       = APIRouter()   # student-facing, registered at /api/<module>
admin_router = APIRouter()   # admin-only,     registered at /api/admin/<module>

# In main.py — both must be imported and registered:
from app.modules.question.router import router as question_router, admin_router as question_admin_router
app.include_router(question_router,       prefix="/api/questions",       tags=["questions"])
app.include_router(question_admin_router, prefix="/api/admin/questions", tags=["admin-questions"])
```

### Security boundary pattern (ADR-012)
```python
# Delivery queries use DB view (excludes correct_option at DB level):
text("SELECT id, exam_id, ... FROM v_exam_questions WHERE exam_id = :eid")
# NEVER: SELECT * FROM questions WHERE exam_id = ...

# Delivery Pydantic schema excludes secure fields (schema-level enforcement):
class QuestionDeliverySchema(BaseModel):
    # correct_option, explanation_en/mr, hint_en/mr NOT declared here
    ...

# Service gate for review (attempt must be submitted):
if attempt["status"] != "submitted":
    raise Forbidden("Review only available after submitting")

# Test verifies schema fields — catches accidental additions:
assert "correct_option" not in QuestionDeliverySchema.model_fields
```

### view() queries via text() in repository
```python
# DB views are queried with text() + explicit column list (never SELECT *)
# asyncpg handles PostgreSQL arrays (TEXT[]) → Python list automatically
_DELIVERY_COLS = "id, exam_id, ..., tags"  # no correct_option

rows = (await db.execute(
    text(f"SELECT {_DELIVERY_COLS} FROM v_exam_questions WHERE exam_id = :eid"),
    {"eid": exam_id},
)).mappings().all()
# rows[0]["tags"] → Python list already
```