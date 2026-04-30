# ScholarPath — Project Knowledge File
# Read this file first before making any code changes.
# Updated: 2026-03-08 | Version: 2.1.0

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
Deploy:    Firebase Hosting (frontend) + Render (backend) + Supabase (DB + Auth)
Media:     Local filesystem (dev) → Cloudinary (prod) via provider pattern
Payment:   Razorpay (orders, subscriptions, webhooks)
```

---

## Module Map (Vertical Slice Architecture)

```
/backend/app/modules/
├── auth/         → JWT + Supabase session bridge, role verification
├── user/         → User profiles, parent-child linking, profile mgmt, password change
├── catalog/      → Exam boards, events, papers, sections, topics
├── question/     → Question bank, options, contexts, bulk import
├── attempt/      → Exam session lifecycle (start → autosave → submit)
├── analysis/     → Scoring engine, topic performance, recommendations, wrong answers
├── media/        → File upload, image serving (provider pattern)
├── payment/      → Razorpay orders, subscriptions, webhooks, access control
└── admin/        → Orchestrator only, zero business logic

/frontend/src/modules/
├── auth/         → Login, register, OAuth callback, ProtectedRoute
├── user/         → OnboardingPage (3-step), ProfilePage (tabbed), OnboardingGuard
├── attempt/      → Exam-taking interface (timer, palette, autosave)
├── analysis/     → Result page, report card, PDF export, WrongAnswerCard, OptionItem
├── dashboard/    → Student home, progress overview
├── parent/       → Parent dashboard, child monitoring, wrong answers review
├── payment/      → UpgradePage, SubscriptionStatus, PaymentResult
└── admin/        → Admin panel, question mgmt, settings, subscriptions
```

---

## Module Boundaries — NEVER Cross These

```
auth      → Owns: auth columns in users table
            Exposes: verify_token(), require_role()
            Consumes: Nothing (no module dependencies)

user      → Owns: user_profiles, parent_student_links
            Exposes: UserService.get_profile(), update_profile(), update_avatar(),
                     change_password(), get_subscription_status()
            Consumes: Auth (verify_token), Media (avatar upload), Payment (subscription)

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
            Exposes: AnalysisService.generate_report(), get_user_performance(),
                     build_wrong_answers_summary()
            Consumes: Attempt (read-only), Question (correct answers + topics)
            RULE: Pure computation. No side effects. No DB writes.

media     → Owns: media_files table
            Exposes: MediaService.upload(), MediaService.delete()
            Consumes: Auth (upload permissions)
            RULE: Swap providers via MEDIA_PROVIDER env var only

payment   → Owns: payment_plans, user_subscriptions, payment_orders, payment_logs,
                   system_settings
            Exposes: PaymentService (Razorpay orders, plan management),
                     AccessControlService.get_access_context(),
                     AccessControlService.can_access_exam()
            Consumes: Auth, User
            RULE: Razorpay webhook handler validates signature before processing.
                  Access control checks are called by attempt module's start_exam.

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

responses.is_correct:   MAY BE NULL even for submitted attempts.
                        The scorer computes correctness at grading time but does
                        NOT always persist it back to individual response rows.
                        NEVER rely on responses.is_correct for wrong answer queries.
                        Instead JOIN v_exam_answers and compare:
                          r.selected_option != va.correct_option

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

### TABLE: payment_plans (ADR-014)
```
id              SERIAL PK
name            VARCHAR(50) NOT NULL
price_inr       INT NOT NULL           -- price in paise
duration_days   INT NOT NULL
max_exams       INT                    -- NULL = unlimited
features        JSONB DEFAULT '[]'
is_active       BOOLEAN DEFAULT true
created_at      TIMESTAMPTZ
```

### TABLE: user_subscriptions (ADR-014)
```
id              SERIAL PK
user_id         UUID FK → user_profiles.id
plan_id         INT FK → payment_plans.id
status          VARCHAR(20) DEFAULT 'active'  -- active, expired, cancelled
started_at      TIMESTAMPTZ
expires_at      TIMESTAMPTZ
cancelled_at    TIMESTAMPTZ
created_at      TIMESTAMPTZ
```

### TABLE: payment_orders (ADR-014)
```
id              SERIAL PK
user_id         UUID FK → user_profiles.id
plan_id         INT FK → payment_plans.id
razorpay_order_id TEXT UNIQUE
amount_inr      INT NOT NULL
status          VARCHAR(20) DEFAULT 'created'  -- created, paid, failed
paid_at         TIMESTAMPTZ
created_at      TIMESTAMPTZ
```

### TABLE: payment_logs (ADR-014)
```
id              SERIAL PK
order_id        INT FK → payment_orders.id
event_type      VARCHAR(50)
payload         JSONB
created_at      TIMESTAMPTZ
```

### TABLE: system_settings (ADR-014)
```
key             VARCHAR(100) PK
value           TEXT NOT NULL
updated_at      TIMESTAMPTZ
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
  authStore    → { user, token, login(), logout(), updateUser(), setLanguage() }
  attemptStore → { currentAttempt, responses, saveResponse(), timer, questionStatus }
  analysisStore→ { report, loading, fetchReport() }
  userStore    → { profile, loadProfile(), updateProfile(), uploadAvatar(),
                   changePassword(), completeOnboarding(), isSaving, saveSuccess }
  parentStore  → { children, selectedChildId, childDetail, loadDashboard(), linkChild() }
  paymentStore → { plans, subscription, loadPlans(), createOrder(), verifyPayment() }

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
| ADR-013 | Child Profile Model | Accepted |
| ADR-014 | Payment & Access Control | Accepted |

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
RAZORPAY_KEY_ID=rzp_test_xxx           # Razorpay API key
RAZORPAY_KEY_SECRET=xxx                # Razorpay secret
RAZORPAY_WEBHOOK_SECRET=xxx            # Razorpay webhook signature secret

# Frontend
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_APP_NAME=ScholarPath
VITE_DEFAULT_LANGUAGE=en
VITE_RAZORPAY_KEY_ID=rzp_test_xxx      # Razorpay publishable key
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

Last updated: 2026-03-08

### Infrastructure (complete)
```
backend/app/main.py              ✅ FastAPI app, CORS (ports 5173+5174), lifespan,
                                    exception handlers, JWKS fetch on startup
                                    Routers registered: user, parent, catalog, question,
                                    question_admin, attempt, analysis, media, admin, payment
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

modules/attempt/   ✅ COMPLETE
modules/analysis/  ✅ COMPLETE
  wrong_answers.py → build_wrong_answers_summary(attempt_id, db, include_details, limit)
                     Queries v_exam_answers (NOT responses.is_correct) to find wrong answers.
                     Compares r.selected_option != va.correct_option.
                     Returns WrongAnswersSummary with total_wrong, total_skipped, items[].
                     Items include: question text/image, selected/correct option,
                     explanation, section_label, topic names, full options list.
                     include_details=False → free tier (counts only, no items).
                     limit=5 → dashboard card (top 5 wrong answers).
  schemas.py       → OptionItemSchema, WrongAnswerItem, WrongAnswersSummary
                     (added: total_skipped, section_label, subject_mr, topic_name_mr)

modules/media/     ✅ COMPLETE
  providers/       → LocalProvider (saves to backend/uploads/, serves /static/)
                     CloudinaryProvider (cloudinary SDK)
                     Swap via MEDIA_PROVIDER env var (ADR-007)
  models.py        → MediaFile
  schemas.py       → MediaUploadResponse
  service.py       → upload(), delete() (delegates to active provider)
  router.py        → POST /api/media/upload (admin only)
  static mount:    → app.mount("/static", ...) in main.py
  aiofiles:        → added to requirements.txt for async local writes

modules/admin/     ✅ COMPLETE
  schemas.py       → AdminOverviewStats, AdminAttemptRow, AdminExamRow,
                     QuestionStatRow, StudentDashboardResponse, StudentDashboardStats
  router.py        → GET  /api/admin/dashboard/overview        (AdminOverviewStats)
                     GET  /api/admin/dashboard/student         (StudentDashboardResponse)
                     GET  /api/admin/dashboard/attempts/recent (AdminAttemptRow[])
                     GET  /api/admin/catalog/exams             (AdminExamRow[])
                     PUT  /api/admin/catalog/exams/{id}/publish
                     PUT  /api/admin/catalog/exams/{id}/unpublish
                     GET  /api/admin/questions/stats?exam_id=X (QuestionStatRow[])
                     GET  /api/admin/settings                  (system settings)
                     PUT  /api/admin/settings                  (update settings)
                     GET  /api/admin/subscriptions             (list subscriptions)
                     POST /api/admin/subscriptions/{id}/cancel (cancel subscription)
  NOTE: Admin is orchestrator only — raw SQL COUNT queries are fine, no business logic

modules/user/      ✅ COMPLETE (core + parent sub-feature + profile management)
  [Core — existing]
  models.py        → UserProfile, ParentStudentLink
  schemas.py       → UserProfileResponse, UpdateProfileRequest (extended: is_onboarded,
                     full_name, phone, school_name, district, date_of_birth, preferred_language,
                     medium, std_class), CompleteProfileRequest, LinkChildRequest,
                     ChangePasswordRequest (with password match validator)
  repository.py    → get_by_id, get_user_id_by_email, update, get_children_with_links,
                     get/create/update_link
  service.py       → get_my_profile, update_my_profile, complete_profile, link_child,
                     update_avatar (updates avatar_url), change_password (Supabase admin),
                     get_subscription_status (delegates to access_control)
  router.py        → GET  /api/users/me
                     PUT  /api/users/me (extended: handles onboarding via is_onboarded flag)
                     POST /api/users/me/complete-profile
                     POST /api/users/me/avatar (2MB, JPEG/PNG/WebP, delegates to MediaService)
                     POST /api/users/me/change-password (email auth users only)
                     GET  /api/users/me/subscription (require_parent)
                     GET  /api/users/my-children
                     POST /api/users/link-child
  tests/           → test_service.py (15 tests), test_router.py

  [Parent sub-feature — added Sessions 1–2, ADR-009]
  parent_schemas.py    → LinkChildRequest, UpdateLinkNicknameRequest,
                         ChildProfileSchema, ChildStatsSchema, ChildAttemptSummarySchema,
                         WeakTopicSchema, ChildDetailSchema, ParentDashboardSchema,
                         RecentMistakesSchema (attempt metadata + WrongAnswersSummary)
  parent_repository.py → get_linked_children, get_link, find_student_by_email,
                         create_link, deactivate_link, update_nickname,
                         get_child_attempts (enforces link check — raises Forbidden),
                         get_child_stats, get_child_topic_performance
                         Singleton: parent_repository = ParentRepository()
                         Cross-module queries (attempts, exams) via text() only — no
                         model imports across module boundaries (AGENTS.md rule)
  parent_service.py    → get_dashboard, get_children, get_child_detail,
                         get_child_attempts_paged, get_child_topics,
                         link_child, update_nickname, unlink_child,
                         get_attempt_wrong_answers (per-attempt review, tier-gated),
                         get_recent_mistakes_summary (dashboard card, top 5, tier-gated)
                         Singleton: parent_service = ParentService()
                         Defence-in-depth: link checked at service level AND inside
                         get_child_attempts() in the repository (ADR-009)
                         Sequential DB calls only — AsyncSession is not concurrency-safe
  parent_router.py     → GET  /api/parent/dashboard         (ParentDashboardSchema)
                         GET  /api/parent/children           (list[ChildProfileSchema])
                         POST /api/parent/children/link      (ChildProfileSchema, 201)
                         GET  /api/parent/children/{id}      (ChildDetailSchema)
                         GET  /api/parent/children/{id}/attempts  (paginated dict)
                         GET  /api/parent/children/{id}/topics    (list[WeakTopicSchema])
                         GET  /api/parent/children/{id}/attempts/{aid}/wrong-answers (WrongAnswersSummary)
                         GET  /api/parent/children/{id}/recent-mistakes (RecentMistakesSchema)
                         PUT  /api/parent/children/{id}/nickname  (ChildProfileSchema)
                         DELETE /api/parent/children/{id}/unlink  ({success: true})
                         All endpoints require require_parent dependency
  tests/           → test_parent_repository.py (20 tests)
                     test_parent_service.py    (17 tests)
                     test_parent_router.py     (25 tests)
                     test_parent_security.py   (17 tests)

modules/payment/   ✅ COMPLETE (ADR-014)
  models.py        → PaymentPlan, UserSubscription, PaymentOrder, PaymentLog, SystemSetting
  schemas.py       → PlanResponse, SubscriptionResponse, CreateOrderRequest/Response,
                     AccessContext
  repository.py    → plan CRUD, subscription CRUD, order lifecycle, access context queries
  service.py       → get_plans, create_order, verify_payment, cancel_subscription,
                     get_access_context, can_access_exam
  router.py        → GET  /api/payment/plans
                     POST /api/payment/create-order
                     POST /api/payment/verify
                     GET  /api/payment/subscription (parent subscription status)
                     POST /api/payment/webhook (Razorpay webhook, no JWT)
  webhook_handler.py → Razorpay signature validation, subscription activation
  razorpay_client.py → Razorpay SDK init
  tests/
```

### Frontend Modules
```
frontend/package.json            ✅ React 18, Vite, Zustand, axios, supabase-js, i18next
frontend/vite.config.js          ✅ @/ alias → ./src
frontend/src/main.jsx            ✅ BrowserRouter with v7_startTransition + v7_relativeSplatPath
frontend/src/App.jsx             ✅ Routes + AuthRedirect + ParentRoute + OnboardingGuard
                                    OnboardingGuard wraps: /profile, /upgrade, /payment/*,
                                    /parent, /parent/children/:studentId
                                    /onboarding NOT wrapped (avoids infinite redirect)
frontend/src/config/
  supabaseClient.js              ✅ createClient with env var validation
  apiClient.js                   ✅ Axios + JWT interceptor + 401 auto-logout
  i18n.js                        ✅ react-i18next setup

modules/auth/                    ✅ COMPLETE
  api/authApi.js                 ✅ getMe(), completeProfile()
  store/authStore.js             ✅ Zustand: initialize(), login(), loginWithGoogle(),
                                    loginWithFacebook(), register(), logout(),
                                    setLanguage(), updateUser() (profile sync)
  pages/LoginPage.jsx            ✅ Email/password + Google + Facebook + redirect if authed
  pages/RegisterPage.jsx         ✅ Email/password registration
  components/ProtectedRoute.jsx  ✅ Redirects unauthenticated users to /login
  index.js                       ✅ Barrel export (OnboardingPage moved to user module)

modules/user/                    ✅ COMPLETE
  api/userApi.js                 ✅ getMe(), updateMe(), uploadAvatar(), changePassword()
  store/userStore.js             ✅ Zustand: loadProfile, updateProfile, uploadAvatar,
                                    changePassword, completeOnboarding, isSaving,
                                    saveSuccess (auto-clears 3s), syncs to authStore.updateUser()
  pages/OnboardingPage.jsx       ✅ 3-step wizard: name/phone → class/district/school → language
                                    Progress bar, animated transitions, calls completeOnboarding
  pages/ProfilePage.jsx          ✅ Two-column: left profile card (avatar, name, email, provider,
                                    subscription) + right tabbed form (Details, Preferences, Password)
                                    Each tab has own Save button + unsaved changes indicator
  components/OnboardingGuard.jsx ✅ Loads profile → spinner while loading → redirect to
                                    /onboarding if is_onboarded=false
  components/AvatarUploader.jsx  ✅ Click-to-upload, two-letter initials fallback, 2MB limit
  components/LanguagePicker.jsx  ✅ Large card grid with flags + checkmarks (EN/MR)
  components/PasswordChangeForm.jsx ✅ Strength bar (weak/medium/strong), onSubmit prop
  index.js                       ✅ Exports: OnboardingPage, ProfilePage, OnboardingGuard,
                                    useUserStore, userApi

shared/layouts/
  AuthLayout.jsx                 ✅ Centered card layout for auth + onboarding pages
  AppLayout.jsx                  ✅ Sidebar + header, avatar image or two-letter initials,
                                    Profile nav link for parents, SubscriptionStatus badge

modules/attempt/   ✅ COMPLETE
  Timer, question palette, autosave, exam shell

modules/analysis/  ✅ COMPLETE
  Result page, topic breakdown, PDF report card (jsPDF + html2canvas)
  components/WrongAnswerCard.jsx → Reusable wrong question card (question text/image,
                                    4 OptionItems with correct/wrong highlighting,
                                    section/topic tags, expandable explanation)
  components/OptionItem.jsx      → Single A/B/C/D option with green (correct),
                                    red (selected wrong), or neutral styling

modules/dashboard/ ✅ COMPLETE
  Student home: available exams, attempt history, performance stats

modules/admin/     ✅ COMPLETE
  AdminRoute guard: checks role ∈ ['exam_admin','super_admin'], shows AccessDenied otherwise
  pages/AdminDashboardPage.jsx    → platform stats (4 count cards + recent activity table)
  pages/QuestionManagerPage.jsx   → 3-tab shell: Browse / Add Question / Import
                                    (tab state only — delegates to 3 sub-components)
  pages/ExamPublisherPage.jsx     → list all exams, publish/unpublish toggle
  pages/ImageUploaderPage.jsx     → upload images for Intelligence Test questions
  pages/StatsPage.jsx             → per-question performance, CSV export
  pages/AdminSettingsPage.jsx     → system settings management
  pages/AdminSubscriptionsPage.jsx→ user subscription management, cancel subscription
  components/QuestionBrowser.jsx  → Browse tab: live exam list (from adminStore.exams),
                                    text search, difficulty/type filters, EN/MR toggle,
                                    expandable rows (full text + options inline),
                                    delete with confirm dialog, edit modal
  components/QuestionTable.jsx    → enhanced: accepts searchTerm prop, EN/MR language
                                    toggle button, 📄 context badge, expandable rows,
                                    correct answer shown as A/B/C/D, delete wired
  components/QuestionCreatorForm.jsx → Add Question tab: single-question form UI
                                    (no JSON needed). Loads sections/topics from
                                    GET /api/catalog/exams/{id} (falls back to manual
                                    ID entry for inactive exams). Auto-suggests Q.No
                                    from max existing in section. Submits via bulkImport.
  components/QuestionImporter.jsx → Import tab: replaces BulkImportButton
                                    JSON + CSV format toggle, Auto/Override exam mode
                                    (fixes exam_id override bug), drag-and-drop zone,
                                    validation preview before import, template downloads
                                    CSV format: one row per question (no context support)
                                    JSON format: full BulkImportSchema (all types)
  components/QuestionEditForm.jsx → enhanced: resizable textareas with char counter,
                                    A/B/C/D option labels with EN+MR display,
                                    note about re-importing to edit option text
  components/BulkImportButton.jsx → DEPRECATED — kept for backward compat but
                                    replaced by QuestionImporter in the UI
  store/adminStore.js             → Zustand store: added deleteQuestion() action
  api/adminApi.js                 → added getExamDetail(examId) for section/topic data

  Key patterns:
    Exam selector uses adminStore.exams (from listAllExams) — includes inactive exams
    Sections/topics fetched from GET /api/catalog/exams/{id} — 404 for inactive →
      falls back to manual numeric input with hardcoded hint text
    BulkImportSchema used for single-question creation (contexts:[], 1-element questions[])
    CSV tags use semicolon (;) separator (comma is field delimiter)

modules/exam/      ⬜ NOT STARTED (catalog browsing — separate from admin)

modules/parent/    ✅ COMPLETE (Sessions 3–5)
  api/parentApi.js             → 10 methods: getDashboard, getChildren, getChildDetail,
                                  getChildAttempts, getChildTopics, createChild,
                                  updateChild, deleteChild,
                                  getAttemptWrongAnswers, getRecentMistakes
  store/parentStore.js         → Zustand: loadDashboard, selectChild, createChild,
                                  updateChild, deleteChild, loadRecentMistakes,
                                  loadAttemptWrongAnswers, clearError, reset
                                  State: children[], selectedChildId, childDetail,
                                  isLoading, isLoadingDetail, isSaving, error, saveError,
                                  wrongAnswersCache (per-attempt), recentMistakes,
                                  loadingWrongAnswers (per-attempt boolean map)
                                  selectChild also calls loadRecentMistakes
  pages/ParentDashboardPage.jsx→ 4 render states: skeleton / error / empty+CTA / main
                                  Child switcher tabs, profile card, weak topics,
                                  RecentMistakesCard, progress chart, attempt history
                                  highlightedAttemptId state + scroll-to-highlight
                                  id="attempt-history" scroll target
  pages/ChildDetailPage.jsx    → Full-page drill-down from :studentId URL param
                                  Profile header, stats grid, weak topics, progress
                                  chart, full paginated attempt history (passes childId)
  components/ChildSwitcher.jsx → Horizontal scrollable tab strip, avatar initials,
                                  class badge, dashed "+ Add" button
  components/ChildProfileCard.jsx → Inline nickname editing (Enter to save), unlink
                                  confirmation dialog, 4 stat boxes (attempts/avg/best/last)
  components/ChildWeakTopics.jsx  → Orange "Needs Attention" + collapsible green
                                  "Strong Areas", TopicBar progress bars, Marathi support
  components/ChildProgressChart.jsx → Recharts LineChart, one line per paper_code,
                                  grade reference lines at 90/70/50%, custom tooltip
  components/ChildAttemptHistory.jsx → Table: score, grade badge, status badge,
                                  "Review Mistakes" ▲/▼ toggle per submitted attempt,
                                  inline AttemptMistakesDrawer expansion,
                                  highlightedAttemptId prop (auto-expand from dashboard),
                                  usePaymentStore for isPaid, client-side pagination
  components/RecentMistakesCard.jsx → Dashboard card with 4 states:
                                  A) No attempts yet
                                  B) Free tier (blurred preview + 🔒 upgrade overlay)
                                  C) Paid tier with wrong answers (MiniWrongAnswerRow cards)
                                  D) Paid tier, all correct (🎉)
                                  MiniWrongAnswerRow: compact ✗/✓ option display + explanation
  components/AttemptMistakesDrawer.jsx → Inline drawer below attempt row,
                                  groups wrong answers by section_label,
                                  reuses WrongAnswerCard from analysis module,
                                  per-attempt loading state, UpgradePrompt for free tier
  components/CreateChildModal.jsx → Child profile creation modal
  index.js                     → Exports all items (2 pages + 9 components +
                                  useParentStore + parentApi)

modules/payment/   ✅ COMPLETE (ADR-014)
  api/paymentApi.js            → getPlans, createOrder, verifyPayment, getSubscription
  store/paymentStore.js        → Zustand: loadPlans, loadStatus, createOrder, verifyPayment
  pages/UpgradePage.jsx        → Plan selection, Razorpay checkout flow
  pages/PaymentSuccessPage.jsx → Success confirmation after payment
  pages/PaymentFailedPage.jsx  → Failure/retry page
  components/SubscriptionStatus.jsx → Badge showing current plan (sidebar + profile page)
  index.js                     → Exports: UpgradePage, PaymentSuccessPage, PaymentFailedPage,
                                  SubscriptionStatus, usePaymentStore, paymentApi
```

### Pending Tasks
```
TODO: Enable Facebook OAuth in Supabase dashboard
      → Authentication → Providers → Facebook (add App ID + Secret)
      → Google OAuth is already enabled and working

TODO: Deploy (Day 14)
      → Firebase Hosting (frontend) + Render (backend) + UptimeRobot keepalive
      → UptimeRobot required to prevent Render free-tier sleep (ADR-008)
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

### Parent module — cross-module data access pattern (ADR-009)
```python
# parent_repository.py reads from attempts + exams via text() raw SQL only.
# NEVER import Attempt or Exam models into the user module.
# The link check fires at BOTH service level AND inside get_child_attempts():
#   service:    link = await parent_repository.get_link(db, parent_id, student_id)
#               if not link: raise Forbidden(...)
#   repository: get_child_attempts() calls get_link() before executing the query
# This double-check is intentional defence-in-depth (ADR-009).

# get_child_attempts raises Forbidden directly — caller does not need to re-check.
# get_child_stats / get_child_topic_performance do NOT check the link —
#   they are internal helpers called only after the link has been verified.

# Sequential DB calls only — a single AsyncSession is not concurrency-safe:
stats_raw   = await parent_repository.get_child_stats(db, student_id)
attempt_rows = await parent_repository.get_child_attempts(db, parent_id, student_id)
topics_raw  = await parent_repository.get_child_topic_performance(db, student_id)
# Do NOT use asyncio.gather() for DB queries sharing the same session.
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

### OnboardingGuard pattern (frontend)
```
OnboardingGuard wraps routes that require is_onboarded=true.
It loads the user profile from /api/users/me, shows a spinner while loading,
and redirects to /onboarding if is_onboarded is false.

Wrap: /profile, /upgrade, /payment/*, /parent, /parent/children/:studentId
Do NOT wrap: /onboarding (causes infinite redirect loop)

The guard uses useUserStore.loadProfile() and syncs with authStore.
```

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"` to keep the graph current

## Graphify Graphs (ScholarPath)

This project has TWO separate graphs. Before running any `/graphify query`, `/graphify path`, or `/graphify explain` command, switch to the correct graph first:

```bash
# Before working on FastAPI/Supabase/Python
./scripts/graphify-switch.sh backend

# Before working on React components/stores/pages
./scripts/graphify-switch.sh frontend
```

Graphs located at:
- `graphify-out/backend/GRAPH_REPORT.md`  → 1,175 nodes, 38 communities (Python backend)
- `graphify-out/frontend/GRAPH_REPORT.md` → 217 nodes, 15 communities (React frontend/src)

`graphify-out/graph.json` is the active graph (whichever was last switched to). Always remind the user to switch if their question is clearly about the other layer.
