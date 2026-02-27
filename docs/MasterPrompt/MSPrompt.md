# SCHOLARPATH — MASTER CONTEXT (TOML)
# Paste this at the start of every Claude Code session.
# Then state: MODULE=x TASK=y

[project]
name = "ScholarPath"
desc = "Multilingual MSCE exam prep portal. Students(5th/8th std) + Parents + Admins"
langs = ["en","mr"]          # mr=Marathi. Add hi later: ALTER TABLE only, no code change
scale = "1 exam now → multi-board, zero code change per new exam"
schema = "/database/scholarpath_migration.sql"
adrs   = "/docs/adr/ADR-001..ADR-012"

[stack]
be  = "Python 3.11 + FastAPI + SQLAlchemy 2.0 async + Alembic"
db  = "PostgreSQL via Supabase (free)"
auth= "Supabase Auth — Google + Facebook + Email. Trigger auto-creates user_profiles"
fe  = "React 18 + Vite + Tailwind 3 + Zustand + react-i18next"
http= "Axios + request interceptor (JWT) + response interceptor (401→logout)"
test= "pytest + pytest-asyncio | Vitest + RTL"
media="LocalProvider(dev) → CloudinaryProvider(prod) via MEDIA_PROVIDER env"
deploy="Vercel(fe) + Render(be) + Supabase(db)"

# ── MODULES ────────────────────────────────────────────────────────────────
# Format: owns | exposes | consumes | hard-rules

[modules.auth]
owns     = "JWT verification, role checks"
exposes  = "verify_token(), require_role()"
consumes = "nothing"
rules    = ["no DB tables", "no profile logic"]

[modules.user]
owns     = "user_profiles, parent_student_links"
exposes  = "UserService.get_profile(), update_profile()"
consumes = "auth.verify_token"
rules    = ["no auth decisions"]

[modules.catalog]
owns     = "exam_boards, exam_categories, exam_events, exams, sections, topics"
exposes  = "CatalogService.get_exam(), list_exams()"
consumes = "auth(admin role check)"
rules    = ["no question data"]

[modules.question]
owns     = "questions, options, question_contexts"
exposes  = "QuestionService.get_questions_for_exam(), validate_answer()"
consumes = "catalog(exam_id), media(image_url)"
rules    = ["NEVER return correct_option in exam delivery — SECURITY BOUNDARY"]

[modules.attempt]
owns     = "attempts, responses, state_machine"
exposes  = "AttemptService.start(), save_response(), submit()"
consumes = "catalog, question, auth"
rules    = ["NO score computation", "NO correct_option reads", "raw storage only", "GOTCHA: QuestionDeliverySchema exposes 'id' (not 'question_id')", "FE uses useAutoSave hook (debounce/dedup)"]

[modules.analysis]
owns     = "NOTHING — read-only"
exposes  = "AnalysisService.generate_report(), get_user_performance()"
consumes = "attempt(read), question(correct answers server-side)"
rules    = ["pure functions only", "NO DB writes", "NO side effects"]

[modules.media]
owns     = "media_files"
exposes  = "MediaService.upload(), delete()"
consumes = "auth(upload perms)"
rules    = ["swap provider via MEDIA_PROVIDER env only"]

[modules.admin]
owns     = "NOTHING — orchestrator only"
exposes  = "/api/admin/* routes"
consumes = "all modules via public interfaces"
rules    = ["ZERO business logic", "delegate only, never own"]

# ── DATABASE ───────────────────────────────────────────────────────────────

[db.rules]
multilingual  = "every text field = column_en + column_mr (TEXT, nullable)"
correct_option= "NEVER in API response during active exam. v_exam_questions excludes it."
scores        = "computed ONCE on submit → stored as JSONB in attempts. Never recompute."
stats         = "question_stats updated by DB trigger only. Never in app code."
rls           = "students=own, parents=linked children via parent_student_links, admins=bypass is_admin()"

[db.views]
v_exam_questions  = "exam delivery — EXCLUDES correct_option + explanation. Always use this."
v_exam_answers    = "post-exam review only — includes correct_option. status=submitted gate."
v_student_attempts= "joins attempts+exams+exam_events. use for dashboard."

[db.triggers]
auto = [
  "questions_updated_at",
  "user_profiles_updated_at",
  "sync_correct_option_trigger — options.is_correct synced from questions.correct_option",
  "update_question_stats_trigger — fires on attempt status→submitted",
  "increment_attempts_used",
  "on_auth_user_created — auto-creates user_profiles on every Supabase signup"
]
rule = "NEVER replicate trigger logic in app code"

[db.rls_helpers]
"is_admin()"                        = "true if role IN (exam_admin, super_admin)"
"is_parent()"                       = "true if role = parent"
"parent_can_see_student(student_id)"= "true if parent_student_links row exists + is_active"

# ── TABLES (exact column names — use these in SQLAlchemy models) ───────────

[db.tables.exam_boards]
cols = "id, name_en, name_mr, short_code VARCHAR(20) UNIQUE, state, website_url, logo_url, is_active, created_at"

[db.tables.exam_categories]
cols = "id, board_id→exam_boards, name_en, name_mr, description_en, description_mr, icon_url, is_active, created_at"

[db.tables.exam_events]
cols = "id, board_id, category_id, title_en, title_mr, std_class SMALLINT, year SMALLINT, exam_date, registration_deadline, description_en, description_mr, is_active DEFAULT false, created_at"

[db.tables.exams]
cols = "id, event_id, paper_code VARCHAR(10), set_code DEFAULT 'A', paper_number, title_en, title_mr, medium medium_type, total_questions DEFAULT 75, total_marks DEFAULT 150, marks_per_question DEFAULT 2, duration_minutes DEFAULT 90, instructions_en, instructions_mr, is_active DEFAULT false, created_at"
unique = "(paper_code, set_code)"

[db.tables.sections]
cols = "id, exam_id, section_label VARCHAR(5), subject_en, subject_mr, question_from SMALLINT, question_to SMALLINT, order_index, color_hex DEFAULT '#3B82F6'"

[db.tables.topics]
cols = "id, section_id, name_en, name_mr, description_en, description_mr, order_index"

[db.tables.question_contexts]
cols = "id, exam_id, context_type context_type, title_en, title_mr, content_en, content_mr, image_url, image_alt_en, image_alt_mr, instruction_en, instruction_mr, applies_from SMALLINT, applies_to SMALLINT, order_index, created_at"

[db.tables.questions]
cols = """
  id, exam_id, section_id, topic_id, context_id→question_contexts(nullable),
  question_no SMALLINT, question_type question_type DEFAULT 'text',
  text_en(nullable), text_mr(nullable),
  question_image_url, question_image_alt_en, question_image_alt_mr,
  correct_option SMALLINT CHECK(1-4),
  explanation_en, explanation_mr, hint_en, hint_mr,
  marks DEFAULT 2, difficulty difficulty_level DEFAULT 'medium',
  tags TEXT[] DEFAULT '{}',
  attempt_count INT DEFAULT 0, correct_count INT DEFAULT 0,
  actual_difficulty_ratio NUMERIC(4,3),
  created_at, updated_at"""
unique = "(exam_id, question_no)"
security = "correct_option NEVER sent to frontend during exam. Server-side only."

[db.tables.options]
cols = "id, question_id, option_no SMALLINT CHECK(1-4), text_en(nullable), text_mr(nullable), image_url(nullable), image_alt_en, image_alt_mr, is_correct BOOLEAN DEFAULT false"
note = "is_correct synced from questions.correct_option by trigger"
unique = "(question_id, option_no)"

[db.tables.user_profiles]
cols = """
  id UUID PK→auth.users(id),
  full_name, role user_role DEFAULT 'student', avatar_url, phone,
  preferred_language VARCHAR(5) DEFAULT 'en',
  std_class SMALLINT, medium medium_type, school_name, district,
  state DEFAULT 'Maharashtra', date_of_birth DATE,
  auth_provider TEXT DEFAULT 'email',
  is_active DEFAULT true, is_onboarded DEFAULT false,
  subscription_tier DEFAULT 'free', subscription_expiry TIMESTAMPTZ,
  created_at, updated_at"""

[db.tables.parent_student_links]
cols = "id, parent_id UUID→user_profiles, student_id UUID→user_profiles, child_nickname, linked_by UUID, linked_at, is_active DEFAULT true"
unique = "(parent_id, student_id)"
check  = "parent_id != student_id"

[db.tables.exam_assignments]
cols = "id, exam_id, student_id UUID, assigned_by UUID(nullable), assignment_type DEFAULT 'practice', max_attempts DEFAULT 10, attempts_used DEFAULT 0, valid_from(nullable), valid_until(nullable), is_active DEFAULT true, created_at"
unique = "(exam_id, student_id)"

[db.tables.attempts]
cols = """
  id UUID PK DEFAULT gen_random_uuid(),
  student_id UUID, exam_id INT, assignment_id INT(nullable),
  attempt_number SMALLINT DEFAULT 1, status attempt_status DEFAULT 'ongoing',
  started_at, submitted_at, last_saved_at, duration_seconds INT,
  total_score SMALLINT, total_correct, total_wrong, total_skipped,
  percentage NUMERIC(5,2), grade VARCHAR(20),
  section_scores JSONB DEFAULT '[]',
  topic_scores   JSONB DEFAULT '[]',
  time_analysis  JSONB DEFAULT '{}',
  recommendations JSONB DEFAULT '[]',
  ip_address INET, user_agent TEXT, created_at"""
jsonb_shapes = """
  section_scores: [{section_id, label, subject_en, subject_mr, correct, total_questions, score, total_marks, percentage}]
  topic_scores:   [{topic_id, name_en, name_mr, correct, total, percentage, status(strong|average|weak)}]
  time_analysis:  {total_time_seconds, avg_per_question, fastest:{q_no,seconds}, slowest:{q_no,seconds}, skipped_count}
  recommendations:[str, ...]"""

[db.tables.responses]
cols = "id BIGSERIAL, attempt_id UUID, question_id INT, question_no SMALLINT, selected_option SMALLINT CHECK(1-4,nullable), is_correct BOOLEAN(nullable), marks_obtained DEFAULT 0, first_visited_at, answered_at, time_taken_seconds SMALLINT, visit_count DEFAULT 0, is_marked_review DEFAULT false"
unique = "(attempt_id, question_id)"

[db.tables.question_stats]
cols = "question_id PK, total_attempts, correct_count, wrong_count, skip_count, avg_time_seconds NUMERIC(6,2), actual_difficulty NUMERIC(4,3), updated_at"
rule  = "updated by DB trigger ONLY — never write from app code"

[db.tables.exam_stats]
cols = "exam_id PK, total_attempts, avg_score, avg_percentage, highest_score, pass_count, updated_at"

[db.tables.notifications]
cols = "id BIGSERIAL, user_id UUID, type VARCHAR(50), title_en, title_mr, body_en, body_mr, data JSONB DEFAULT '{}', is_read DEFAULT false, read_at, created_at"

[db.tables.enquiries]
cols = "id, name, email, phone, school_name, district, std_class, message, status enquiry_status DEFAULT 'new', admin_notes, responded_by UUID, responded_at, source DEFAULT 'website', referral_code, created_at"

[db.enums]
user_role       = ["student","parent","teacher","exam_admin","super_admin"]
medium_type     = ["english","marathi","hindi","semi_english"]
question_type   = ["text","text_image","image_only","context_text","context_image","marathi_only","bilingual"]
attempt_status  = ["ongoing","submitted","expired","abandoned"]
assignment_type = ["practice","assigned","mock_test"]
context_type    = ["paragraph","poem","advertisement","image","pictograph","instruction","venn_diagram","figure_series","table","data_chart"]
difficulty_level= ["easy","medium","hard"]
enquiry_status  = ["new","contacted","resolved","spam"]

[db.indexes]
questions   = ["(exam_id)","(exam_id,question_no)","(section_id)","(topic_id)","(context_id)"]
responses   = ["(attempt_id)","(question_id)"]
attempts    = ["(student_id)","(exam_id)","(student_id,exam_id)","(status)","(submitted_at DESC)"]
assignments = ["(student_id)","(exam_id)"]
links       = ["(parent_id)","(student_id)"]
notifs      = ["(user_id)","(user_id,is_read) WHERE is_read=false"]

[db.seed]
exam_boards      = "1 row: MSCE Maharashtra"
exam_categories  = "1 row: Pre-Upper Primary Scholarship"
exam_events      = "1 row: MSCE 5th Std 2025"
exams            = "2 rows: Paper 501 + Paper 502"
sections         = "4 rows: I+II per paper"
topics           = "26 rows: Grammar, Fractions, Mirror Images etc"

# ── EXAM DOMAIN ────────────────────────────────────────────────────────────

[exam.structure]
"Paper 0501" = "Sec-I Q1-25 English | Sec-II Q26-75 Mathematics"
"Paper 0502" = "Sec-I Q1-25 Marathi | Sec-II Q26-75 Intelligence Test"
questions    = 75
marks_each   = 2
total_marks  = 150
duration_min = 90
marking      = "correct=+2 wrong=0 skipped=0 (NO negative marking)"

[exam.grades]
"Excellent"   = ">= 90%"
"Good"        = ">= 70%"
"Average"     = ">= 50%"
"Below Average"= "< 50%"

[exam.topic_status]
strong  = ">= 70%"
average = ">= 50%"
weak    = "< 50%  → triggers recommendation"

[exam.attempt_states]
transitions = {not_started=["ongoing"], ongoing=["submitted","expired","abandoned"], submitted=[], expired=[], abandoned=["ongoing"]}
terminal    = ["submitted","expired"]

[exam.palette_colors]
"not-visited"    = "visit_count=0 → gray bg-gray-200"
"visited"        = "visit_count>0, no answer → white border-gray-400"
"answered"       = "selected_option set, not marked → green bg-green-500"
"marked"         = "is_marked_review=true, no answer → orange bg-orange-400"
"marked-answered"= "is_marked_review=true + answer → purple bg-purple-500"
"current"        = "ring-2 ring-blue-600 (added to any status)"

# ── CODE STANDARDS ─────────────────────────────────────────────────────────

[code.backend]
file_order   = "models → schemas → repository → repository_test → service → service_test → router → router_test"
queries      = "ALL DB queries in repository.py ONLY"
logic        = "ALL business logic in service.py ONLY"
router_rule  = "router calls service ONLY — no direct DB, no logic"
async        = "async/await on EVERY DB operation (SQLAlchemy 2.0 async)"
exceptions   = "raise specific exceptions from shared/exceptions.py — never bare HTTPException in service"
multilingual = "every text field = field_en + field_mr, never field: str alone"
lang_util    = "from app.shared.i18n import get_text — get_text(obj, lang, field)"
migrations   = "NEVER generate — describe changes, human reviews and runs"

[code.frontend]
components   = "functional only, Tailwind only (no inline styles)"
state        = "Zustand — one store per module, always include isLoading+error+reset()"
api_calls    = "always through apiClient.js — never raw fetch/axios"
routing      = "role-aware POST-LOGIN redirect (parent→/parent, students→/dashboard). AppLayout sidebar varies by role."
hooks        = "React Rules of Hooks strict adherence: all useStates BEFORE conditional returns (e.g. guarded auth pages)."
exports      = "each module exports ONLY through index.js (pages, stores, api)"
i18n         = "t() for ALL UI strings — never hardcode English text in JSX"
loading      = "every data-fetching component needs loading + error state"
autosave     = "optimistic update first, API call fire-and-forget"
stores_outside= "useStore.getState() to read store outside React components"

[code.testing]
required_per_module = ["unit(service, mocked repo)", "integration(router, TestClient)", "security(auth boundaries)"]
security_tests = [
  "test_correct_option_not_in_exam_delivery",
  "test_student_cannot_access_other_student_data",
  "test_parent_cannot_see_unlinked_child",
  "test_admin_endpoint_blocked_for_student",
  "test_review_blocked_for_ongoing_attempt"
]
scorer_coverage = "100% — pure functions, no DB, no excuses"

# ── AI BOUNDARIES ──────────────────────────────────────────────────────────

[ai.do]
freely = [
  "scaffold: models, schemas, repos, services, routers",
  "boilerplate: logging, error handling, config, DI",
  "tests: unit + integration + security stubs",
  "docs: README per module, docstrings, API examples",
  "refactor: rename, restructure, deduplicate",
  "frontend: components, stores, API hooks, i18n keys",
  "SQL: standard CRUD in repository.py"
]

[ai.never]
touch = [
  "module boundaries (set in ADRs — not negotiable)",
  "DB migrations (describe → human reviews → human runs)",
  "auth + RLS logic (security-critical)",
  "scoring thresholds (business logic)",
  "correct_option in exam delivery (security boundary ADR-012)",
  "media provider selection (ADR-007)",
  "cross-module internal imports",
  "DB queries outside repository.py",
  "business logic in admin module",
  "scores computed in attempt module"
]

[ai.workflow]
"1_load_context"  = "read CLAUDE.md → read relevant ADR → read module README → confirm scope"
"2_adr_check"     = "existing ADR? follow it. missing? STOP, flag, human writes ADR first"
"3_contract_first"= "write + show schemas BEFORE repository/service/router"
"4_scaffold"      = "one module at a time, file order above"
"5_guardrails"    = "verify checklist after every file"
"6_ship_slice"    = "API + frontend component + tests = done. never ship partial"
"7_document"      = "update module README after every task"

[ai.checklist]
before_done = [
  "all DB queries in repository.py only",
  "no correct_option in any exam delivery response",
  "multilingual pairs on all new content fields",
  "no cross-module internal imports",
  "async throughout backend",
  "specific exceptions raised",
  "unit + integration + security tests written",
  "module README updated",
  "loading+error states in all frontend data components",
  "no hardcoded strings (use t())"
]

# ── SESSION START FORMAT ────────────────────────────────────────────────────

[session]
format = """
MODULE:      [auth|user|catalog|question|attempt|analysis|media|admin]
TASK TYPE:   [scaffold|feature|test|refactor|fix|docs]
ADR:         [ADR-XXX]
TASK:        one clear sentence
CREATE:      list of files to create
MODIFY:      list of files to modify
NO TOUCH:    files/modules that must not change
DONE WHEN:   acceptance criteria
"""

# ── ENVIRONMENT VARIABLES ───────────────────────────────────────────────────

[env.backend]
DATABASE_URL          = "postgresql+asyncpg://user:pass@host/scholarpath"
SUPABASE_URL          = "https://xxx.supabase.co"
SUPABASE_JWT_SECRET   = "from Supabase → Settings → API → JWT secret"
SUPABASE_SERVICE_KEY  = "service role key"
MEDIA_PROVIDER        = "local | cloudinary"
BASE_URL              = "http://localhost:8000"

[env.frontend]
VITE_API_URL          = "http://localhost:8000"
VITE_SUPABASE_URL     = "https://xxx.supabase.co"
VITE_SUPABASE_ANON_KEY= "anon key"
VITE_DEFAULT_LANGUAGE = "en"

# ── BUILD PHASES ────────────────────────────────────────────────────────────

[phases]
done = [
  "Day1:FastAPI+Auth", "Day2:User", "Day3:FE-Auth", "Day4:Catalog",
  "Day5:Question (models + security)", "Day7:Attempt (state + api)", 
  "Day8:Exam UI", "Day9:Analysis", "Day10:Result + PDF", 
  "Day11:Student dashboard", "Day12:Parent dashboard", "Day13:Admin panel"
]
next = [
  "Day6:  Seed 150 MSCE questions via importer (Pending Data Task)",
  "Day14: Deploy Vercel + Render + UptimeRobot keepalive"
]
rule = "complete verification checklist before advancing to next day"

# ── ADR INDEX ───────────────────────────────────────────────────────────────

[adrs]
"ADR-001" = "Authentication — Supabase Auth, Google+Facebook+Email, trigger auto-profile"
"ADR-002" = "Vertical Slice Architecture — module contracts, one module per session"
"ADR-003" = "Multilingual — _en/_mr column pairs, get_text() util, ALTER TABLE for new langs"
"ADR-004" = "Question Content Model — 7 types, question_contexts shared, options separate"
"ADR-005" = "Attempt State Machine — per-answer upsert, resume on refresh, server timer"
"ADR-006" = "Score Computation — pure functions, store JSONB on submit, never recompute"
"ADR-007" = "Media Provider Pattern — LocalProvider dev, CloudinaryProvider prod, env swap"
"ADR-008" = "Supabase Platform — free tier, RLS native, UptimeRobot keepalive required"
"ADR-009" = "Parent-Student Auth — join table, parent_can_see_student() RLS helper"
"ADR-010" = "Frontend Zustand Stores — one per module, optimistic updates, no WebSockets"
"ADR-011" = "Exam Scalability — 4-level hierarchy, new exam = data only, no code"
"ADR-012" = "Answer Security — v_exam_questions view, correct_option server-side only"