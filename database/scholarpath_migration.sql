CCC_0501_V_English_P_1_25_A.pdf pdf CCC_0502_V_English_II_25_A.pdf pdf i am preparing website for exam for the 5th
and the 8th class scholar ship for indian students.there will be multi language exams.lets work
and build architecture for the website.We have 2 question papers.I am attaching the pdf for previsou year exam.We want detail implementation.plan for this.understand this think hard
and discuss the plan.it should be multilingula.We need backedn front
end
and deployment.lets discuss all the plan in detail for implimentation.I want a detail crafted prompt for this to develop the exam.This online exam should be 2
).Which game requires a racket for playing it (कोणता खेळ खेळण्याकरिता रॅकेट ची गरज असते ?) * 2 points Chess Cricket Hockey Tennis like this one of the example.
When we submit it should give the detail analysis of the exam.as a best exam prepration which help student for enhans in his educatoin build a plan.Then i can use work on the coding..use free technologies.also take rerance
from exam website to build better plan Show more Feb 17 Architected multilingual exam platform with React,
    FastAPI,
    PostgreSQL,
    and free deployment solutions Architected multilingual exam platform with React,
    FastAPI,
    PostgreSQL,
    and free deployment solutions 🎓 Scholarship Exam Portal — Full Architecture & Implementation Plan Great choice ! I 've carefully studied both PDFs. Let me give you a comprehensive, detailed plan before writing the Claude Code prompt.

📋 Exam Structure Analysis (from PDFs)
Paper 1 (0501): English (Q1–25) + Mathematics (Q26–75) = 75 Qs × 2 marks = 150 marks, 90 min

Paper 2 (0502): Marathi/Third Language (Q1–25) + Intelligence Test (Q26–75) = 75 Qs × 2 marks = 150 marks, 90 min

Key observations:

MCQ with 4 options
Questions include: paragraphs, poems, advertisements, pictographs, Venn diagrams, mirror/water images, number series
Multilingual: English questions, Marathi questions, bilingual questions (like your tennis example)
5th Standard + 8th Standard (different paper sets)
🛠️ Free Tech Stack
Layer	Technology	Why Free
Frontend	React + Vite + Tailwind CSS	Open source
Backend	Python FastAPI	Open source
Database	PostgreSQL via Supabase	Free tier (500MB)
Auth	Supabase Auth	Free tier
Image/PDF Storage	Cloudinary	Free tier (25GB)
Deployment (FE)	Vercel	Free tier
Deployment (BE)	Render.com	Free tier
i18n	react-i18next	Open source
Charts (Analysis)	Recharts	Open source
PDF export	jsPDF	Open source
🏗️ Complete System Architecture
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                   │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────┐  │
│  │ Landing  │ │  Login/  │ │   Exam    │ │  Analysis    │  │
│  │  Page    │ │ Register │ │  Portal   │ │  Dashboard   │  │
│  └──────────┘ └──────────┘ └───────────┘ └──────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST API / HTTP
┌───────────────────────▼─────────────────────────────────────┐
│                   BACKEND (FastAPI Python)                   │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────┐  │
│  │   Auth   │ │Questions │ │   Exam    │ │   Reports    │  │
│  │  Routes  │ │   CRUD   │ │  Engine   │ │   Engine     │  │
│  └──────────┘ └──────────┘ └───────────┘ └──────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              DATABASE (Supabase PostgreSQL)                  │
│  users │ exams │ questions │ options │ attempts │ responses  │
└─────────────────────────────────────────────────────────────┘
🗄️ Database Schema Design
sql
-- Users
users: id, name, email, password_hash, std_class (5/8), 
       medium (english/marathi/hindi/semi-english), 
       school_name, district, created_at

-- Exams  
exams: id, title, paper_code (0501/0502), std_class, 
       year, total_marks, duration_minutes, 
       is_active, created_at

-- Subjects
subjects: id, exam_id, name_en, name_mr, name_hi, 
          q_from, q_to (e.g. 1-25, 26-75)

-- Questions
questions: id, exam_id, subject_id, question_no, 
           text_en, text_mr, text_hi,
           question_type (mcq/image_mcq/passage_mcq),
           image_url, passage_id, marks, correct_option

-- Passages (for reading comprehension)
passages: id, exam_id, text_en, text_mr, q_from, q_to

-- Options
options: id, question_id, option_no (1/2/3/4), 
         text_en, text_mr, text_hi, image_url

-- Exam Attempts
attempts: id, user_id, exam_id, started_at, 
          submitted_at, total_score, status (ongoing/submitted)

-- Responses
responses: id, attempt_id, question_id, 
           selected_option, is_correct, time_taken_sec
```

---

## 📱 Frontend Pages & Features

### 1. Landing Page
- Hero with exam info (5th / 8th scholarship)
- Language selector (English / मराठी / हिंदी)
- Login / Register buttons
- Previous year papers section

### 2. Student Dashboard
- Upcoming/available exams
- Past attempt history with scores
- Performance trends (graph)
- Weak topic recommendations

### 3. Exam Interface (Most Critical)
```
┌─────────────────────────────────────────────────┐
│  MSCE Scholarship | Paper 1 | 00:45:32 ⏱️       │
│  English ████████████░░░  Mathematics            │
├──────────────┬──────────────────────────────────┤
│  Q 1-25 grid │  Q.12                            │
│  ■ ■ □ ■ ■  │                                  │
│  □ ■ ■ □ ■  │  कोणता खेळ खेळण्याकरिता          │
│  ■ □ ■ ■ □  │  रॅकेटची गरज असते?               │
│  ■ ■ □ □ ■  │  Which game requires a racket?   │
│             │                                  │
│  Q 26-75 grid│  ○ (1) Chess / बुद्धिबळ         │
│  □ □ □ □ □  │  ○ (2) Cricket / क्रिकेट         │
│             │  ○ (3) Hockey / हॉकी              │
│  Legend:    │  ● (4) Tennis / टेनिस  ✓         │
│  ■ Answered │                                  │
│  □ Skipped  │  [← Prev]  [Mark Review]  [Next→]│
└─────────────┴──────────────────────────────────┘
│  [Submit Exam]                                  │
└─────────────────────────────────────────────────┘
```

**Features:**
- Timer with auto-submit
- Question palette (color-coded: answered/skipped/marked for review)
- Bilingual display toggle
- Image-based questions support
- No back navigation after submit warning

### 4. Post-Exam Analysis Dashboard (Key Differentiator)
```
┌─────────────────────────────────────────────────┐
│  📊 Your Exam Report — Paper 1 | Preetam Jr.    │
├─────────────┬───────────────────────────────────┤
│  SCORE      │  SUBJECT BREAKDOWN                │
│  118 / 150  │  English:    38/50  ████████░░    │
│  78.6%      │  Mathematics:80/100 ████████░░    │
│  🏆 Good    │                                   │
├─────────────┴───────────────────────────────────┤
│  ACCURACY   |  TIME ANALYSIS                    │
│  Correct:59 |  Avg per Q: 1:12 min              │
│  Wrong:  12 |  Fastest: Q3 (0:15s)              │
│  Skipped: 4 |  Slowest: Q47 (3:40s)             │
├─────────────────────────────────────────────────┤
│  TOPIC-WISE PERFORMANCE                         │
│  Grammar         ████████░░  80%  ✅ Strong      │
│  Comprehension   ██████░░░░  60%  ⚠️ Average    │
│  Fractions       ████░░░░░░  40%  ❌ Weak        │
│  Profit & Loss   ██████░░░░  60%  ⚠️ Average    │
│  Intelligence    ████████░░  80%  ✅ Strong      │
├─────────────────────────────────────────────────┤
│  QUESTION REVIEW  (Wrong Answers Highlighted)   │
│  Q.12 ❌ You: Chess  ✓ Correct: Tennis          │
│  Q.34 ❌ You: 560    ✓ Correct: ₹560            │
├─────────────────────────────────────────────────┤
│  🎯 RECOMMENDATIONS                             │
│  • Practice more Fraction problems (Q28, Q45)   │
│  • Revise Profit & Loss concepts                │
│  • You' re strong in Intelligence Test ! │ ├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┤ │ [📄 Download PDF Report] [🔄 Retake Exam] │ └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘ 5.Admin Panel Upload questions (
        manual
        or CSV / JSON import
    ) Manage exams (activate / deactivate) View all student reports Bulk question upload
from PDF 🌐 Multilingual Implementation javascript // react - i18next structure / locales / en common.json // buttons,
    labels exam.json // exam interface text / mr common.json // मराठी exam.json / hi common.json // हिंदी exam.json // Questions stored in DB with en / mr / hi columns // User selects medium → API returns correct language ```

**Language Support:**
- English Medium
- Marathi Medium  
- Hindi Medium
- Semi-English (Marathi with English terms)

---

## 🚀 Deployment Plan (All Free)
``` GitHub (code) ↓ auto - deploy Vercel (React frontend) → yourdomain.vercel.app ↓ API calls Render.com (FastAPI) → api.yourdomain.render.com ↓ DB queries Supabase (PostgreSQL) → free 500MB ↓ media Cloudinary (images) → free 25GB ```

---

## 📝 Claude Code Implementation Prompt

Here's the detailed prompt you can use directly with Claude Code:

---

**PROMPT:**
``` Build a complete multilingual online exam preparation website for Indian students (
        5th
        and 8th class Maharashtra Scholarship Exam - MSCE Pre - Upper Primary & Pre - Secondary Scholarship
    ).## PROJECT NAME: ScholarPath (or use "vidyarthi-exam-portal")
    ## TECH STACK (all free/open-source):
    - Frontend: React 18 + Vite + Tailwind CSS + react - i18next - Backend: Python FastAPI + SQLAlchemy - Database: PostgreSQL (use SQLite for local dev) - Auth: JWT tokens (python - jose) - Charts: Recharts - PDF: jsPDF + html2canvas - Deployment - ready for: Vercel (FE) + Render (BE) + Supabase (DB) ## EXAM STRUCTURE (reference):
    Based on MSCE Maharashtra Scholarship Exam: - Paper 1 (0501): Section I = First Language (Q1 -25),
    Section II = Mathematics (Q26 -75) - Paper 2 (0502): Section I = Third Language Marathi (Q1 -25),
    Section II = Intelligence Test (Q26 -75) - Each paper: 75 questions × 2 marks = 150 marks,
    90 minutes - Format: MCQ with 4 options (
        A / B / C / D
        or 1 / 2 / 3 / 4
    ) - Classes: Standard 5th
    and Standard 8th - Languages: English,
    Marathi,
    Hindi ## DATABASE SCHEMA:
    Create these tables with SQLAlchemy models: 1.users(
        id,
        name,
        email,
        password_hash,
        std_class,
        medium,
        school_name,
        district,
        role,
        created_at
    ) 2.exams(
        id,
        title_en,
        title_mr,
        paper_code,
        std_class,
        year,
        total_marks,
        duration_minutes,
        is_active
    ) 3.subjects(
        id,
        exam_id,
        name_en,
        name_mr,
        name_hi,
        question_from,
        question_to
    ) 4.passages(
        id,
        exam_id,
        text_en,
        text_mr,
        text_hi,
        question_from,
        question_to
    ) 5.questions(
        id,
        exam_id,
        subject_id,
        question_no,
        text_en,
        text_mr,
        text_hi,
        question_type,
        image_url,
        passage_id,
        marks,
        correct_option
    ) 6.options(
        id,
        question_id,
        option_no,
        text_en,
        text_mr,
        text_hi,
        image_url
    ) 7.attempts(
        id,
        user_id,
        exam_id,
        started_at,
        submitted_at,
        total_score,
        percentage,
        status
    ) 8.responses(
        id,
        attempt_id,
        question_id,
        selected_option,
        is_correct,
        marks_obtained,
        time_taken_seconds
    ) 9.topics(id, subject_id, name_en, name_mr, question_ids) ## BACKEND API ENDPOINTS (FastAPI):
    AUTH: - POST / api / auth / register - POST / api / auth / login - GET / api / auth / me EXAMS: - GET / api / exams (list active exams by class) - GET / api / exams / { exam_id } (exam details) - GET / api / exams / { exam_id } / questions (all questions with options) ATTEMPTS: - POST / api / attempts / start (create new attempt, return attempt_id) - POST / api / attempts / { attempt_id } / submit (submit exam) - GET / api / attempts / { attempt_id } / result (detailed result) - GET / api / attempts / history (
        user 's past attempts)

ANALYSIS:
- GET  /api/analysis/{attempt_id}/report (full analysis)
- GET  /api/analysis/user/performance (overall stats)

ADMIN:
- POST /api/admin/questions (create question)
- POST /api/admin/questions/bulk (JSON bulk upload)
- GET  /api/admin/reports (all student reports)

## FRONTEND PAGES:

1. LANDING PAGE (/)
   - Hero section with exam info cards (5th / 8th scholarship)
   - Language selector dropdown (English/मराठी/हिंदी) in navbar
   - Features section (timer, analysis, bilingual)
   - Sample question preview
   - Login/Register CTA buttons
   - Previous year papers download links

2. AUTH PAGES (/login, /register)
   - Student registration with: name, email, password, class (5/8), 
     medium (English/Marathi/Hindi/Semi-English), school, district
   - Login form
   - JWT stored in localStorage

3. STUDENT DASHBOARD (/dashboard)
   - Welcome banner with student name and class
   - Available exams grid (Paper 1, Paper 2 for their class)
   - Performance summary cards: Total Attempts, Avg Score, Best Score
   - Recent attempts table with scores
   - Line chart of score progress over time (Recharts)
   - Weak topics highlight section

4. EXAM INTERFACE (/exam/:exam_id) - MOST IMPORTANT:
   
   LAYOUT:
   - Top bar: Exam name | Section indicator | Countdown timer (HH:MM:SS)
   - Left sidebar (30% width): Question number grid palette
     * Color coding: 
       - Gray = Not visited
       - White with border = Visited but not answered
       - Green = Answered
       - Orange = Marked for review
       - Purple = Answered + Marked for review
     * Sections shown separately (Section I and Section II)
   - Main area (70% width): Current question display
   - Bottom: [← Previous] [Mark for Review ⭐] [Save & Next →]
   - Top right: [Submit Exam] button (with confirmation dialog)
   
   QUESTION DISPLAY:
   - Question number and marks indicator
   - Language toggle button (show EN / MR / HI based on user' s medium
    ) - For passage questions: show passage in collapsed / expandable panel - For image questions: display image with zoom option - 4 radio button options with hover effects - Selected option highlights in blue - Clear response button TIMER BEHAVIOR: - Counts down
from 90 :00 - Yellow warning at 10 minutes - Red warning at 5 minutes - Auto - submit
    when timer reaches 0 - Store responses every 30 seconds (auto - save to prevent data loss) SUBMIT FLOW: - Show summary modal: X answered,
    Y unanswered,
    Z marked for review - Confirm submit button - Redirect to result page 5.RESULT PAGE (/ result / :attempt_id): SECTION 1 - SCORECARD: - Large score display: 118 / 150 (78.6 %) - Grade badge: Excellent / Good / Average / Below Average - Donut chart: Correct vs Wrong vs Unattempted SECTION 2 - SUBJECT BREAKDOWN: - Table: Subject | Score | Percentage | Progress bar - Compare with class average (if available) SECTION 3 - TIME ANALYSIS: - Total time taken - Average time per question - Fastest
    and slowest questions - Time distribution bar chart SECTION 4 - TOPIC - WISE PERFORMANCE: - Table with topics,
    score,
    percentage,
    status (Strong / Average / Weak) - Color coded (green / yellow / red) SECTION 5 - QUESTION REVIEW: - Expandable accordion for each question - Show: Your answer (wrong = red, correct = green) | Correct answer - Show explanation if available - Filter: All | Wrong Only | Correct Only SECTION 6 - RECOMMENDATIONS: - Auto - generated based on weak topics - "You scored less than 50% in Fractions. Practice Q28, Q45 type questions" - Study tips specific to exam type ACTIONS: - Download PDF Report button (jsPDF) - Retake Exam button -
Go to Dashboard button 6.ADMIN PANEL (/ admin): - Login separately with admin role - Exam management: Create / Edit / Delete exams - Question management:
Add / Edit / Delete questions - Bulk question upload via JSON file - Student reports table with filters - Export reports to CSV ## MULTILINGUAL IMPLEMENTATION:
    - Use react - i18next - Create / locales / en / translation.json,
    / locales / mr / translation.json,
    / locales / hi / translation.json - All UI labels,
    buttons,
    messages in all 3 languages - Questions fetched with language parameter
from API - User 's preferred medium stored in profile and used as default
- Language switcher in navbar (persists to localStorage)

## SEED DATA:
Create seed script with sample data including:
1. One complete exam (Paper 1) with 10 sample questions from the MSCE pattern:
   
   Sample questions to include:
   
   Q1 (English - Passage MCQ):
   text_en: "Bal Gandharva was one of the most famous actors in India..."
   [Include Q1 and Q2 from passage about Bal Gandharva]
   
   Q3 (English - Poem MCQ):  
   text_en: "Read the poem ' The House Next Door ' and answer..."
   
   Q6 (English - Grammar):
   text_en: "There are twelve months in a year. August is ________ month."
   text_mr: "वर्षात बारा महिने असतात. ऑगस्ट हा ________ महिना आहे."
   options: eighth, eight, seventh, seven
   correct: 1 (eighth)
   
   Q26 (Math - Weight):
   text_en: "23 kg 500 gm + 21 kg 750 gm = ?"
   options: 45kg 250gm, 45kg 750gm, 44kg 250gm, 44kg 750gm
   correct: 1
   
   Q34 (Math - Simple Interest):
   text_en: "What is the simple interest on ₹3500 at 8% p.a. for 2 years?"
   options: ₹280, ₹560, ₹480, ₹260
   correct: 2

   Intelligence Test example:
   text_en: "Which game requires a racket for playing it?"
   text_mr: "कोणता खेळ खेळण्याकरिता रॅकेटची गरज असते?"
   options_en: Chess, Cricket, Hockey, Tennis
   options_mr: बुद्धिबळ, क्रिकेट, हॉकी, टेनिस
   correct: 4 (Tennis)

2. Create 2 test users (student + admin)

## ADDITIONAL FEATURES:
- Practice Mode: Untimed exam with hints
- Mock Test Mode: Timed exam simulating real exam
- Previous Year Papers section
- Leaderboard (optional, top 10 scorers per exam)
- Email notifications (using SMTP - free Gmail)

## RESPONSIVE DESIGN:
- Mobile-first approach
- Exam interface works on tablets and mobile
- Question palette collapses to bottom drawer on mobile
- Minimum screen tested: 375px (iPhone SE)

## PROJECT STRUCTURE:
/scholarship-exam-portal
├── /frontend
│   ├── /src
│   │   ├── /components
│   │   │   ├── /exam (ExamInterface, QuestionPalette, Timer, QuestionCard)
│   │   │   ├── /result (ScoreCard, TopicAnalysis, QuestionReview)
│   │   │   ├── /layout (Navbar, Sidebar, Footer)
│   │   │   └── /common (Button, Modal, LanguageSwitch)
│   │   ├── /pages (Landing, Dashboard, Exam, Result, Admin, Login)
│   │   ├── /store (Zustand for exam state management)
│   │   ├── /services (API calls with Axios)
│   │   ├── /locales (en, mr, hi translations)
│   │   └── /utils (timer, score calculator)
│   ├── vite.config.js
│   └── package.json
├── /backend
│   ├── /app
│   │   ├── /models (SQLAlchemy models)
│   │   ├── /schemas (Pydantic schemas)
│   │   ├── /routes (auth, exams, attempts, analysis, admin)
│   │   ├── /services (exam_service, report_service, auth_service)
│   │   └── main.py
│   ├── /alembic (DB migrations)
│   ├── seed.py
│   └── requirements.txt
└── docker-compose.yml (optional for local dev)

## DEPLOYMENT CONFIG:
- Create vercel.json for frontend
- Create render.yaml for backend  
- Environment variables documentation in .env.example
- README with setup instructions

Build the complete working application with all the above features. 
Start with the database models and API, then build the frontend. 
Include proper error handling, loading states, and form validation throughout.
🗺️ Development Phases
Phase 1 (Week 1-2): DB schema + FastAPI backend + Auth + Questions API

Phase 2 (Week 3-4): React frontend — Landing, Dashboard, Exam Interface

Phase 3 (Week 5): Result Analysis page + PDF report

Phase 4 (Week 6): Admin panel + Multilingual (i18n) + Question bulk upload

Phase 5 (Week 7): Deployment + seed data + testing

💡 Key Differentiators vs Other Exam Sites
Inspired by sites like Testbook, BYJU' s,
    and Unacademy: Bilingual questions — show both English & Marathi simultaneously Deep analysis — topic - wise not just total score Question review — see correct answer with explanation Time analysis — know which questions took too long Exam - specific tips — tailored to MSCE pattern Offline - ready — PWA support later The prompt above is ready to paste directly into Claude Code.Want me to start building any specific piece right now — like the database models,
    the exam interface React component,
    or the analysis engine ? As this project is going to scale so can we modularize this implimentation so that it can scale
after ti gets bigger.i have return the article on this.think on this
    and mold the prompt accordingly L;
DR I use AI coding tools for scaffolding,
tests,
docs,
and boring boilerplate.Architecture
and module boundaries stay human ‑ led.We broke the app into small vertical slices,
added guardrails,
and shipped faster.The Real Problem Large applications slow down as complexity grows.Code reviews take longer as dependencies multiply.Once the codebase exceeds the model ’ s context window,
AI becomes unreliable.I worked on a similar application
and learned how to keep a mid ‑ to ‑ large system clean as it scales.The Core Approach Break the application into small,
focused modules (Auth, Payments, Notifications, Search, etc.).Give each module a clear contract (OpenAPI, AsyncAPI, typed interfaces).Boundaries — What belongs inside each module Communication patterns — REST,
events,
or shared types Data ownership & consistency — including CDC
when needed Cross ‑ cutting guardrails — auth,
security,
rate limits,
uptime Testing strategy Security testing Repo + delivery strategy
Where to avoid using AI
Where AI Helps (
        and
        Where It Doesn ’ t
    )
Where AI Helps Scaffolding: controllers,
    services,
    repositories,
    DTOs,
    validation pipelines Boilerplate: logging,
    error handling,
    config,
    DI,
    authorization setup Tests: unit tests,
    contract tests,
    test data,
    basic security tests Documentation: READMEs,
    API examples,
    module guides Refactoring: renaming,
    restructuring,
    cleanup
Where AI Hurts Architecture decisions Complex business logic (edge cases, conditions, failure modes) Security ‑ critical components Anything involving sensitive code AI is an assistant — not the architect.Pros Speed: huge boost for repetitive work Consistency: cleaner naming
    and patterns Source control: easier merges
    and commit hygiene with structured prompts Better documentation: faster to create
    and
update Less time wasted on syntax issues Cons Quality drift: code looks right but isn ’ t safe Contract drift: modules misalign if not enforced Shallow tests: AI defaults to happy paths Privacy & licensing concerns Architecture erosion: quick fixes break long ‑ term integrity Without reviews,
    expertise,
    contract tests,
    and security checks,
    you ’ ll hit a wall.My Workflow Strong context + knowledge files (clean system prompt, templates, cleanup routines) One ‑ page module ADRs for Users,
    Auth,
    Payments,
    Notifications,
    Search Contracts ‑ first approach using OpenAPI + AsyncAPI Scaffold with AI — one module at a time
Add guardrails (
        coding standards,
        formatting,
        security scans,
        contract tests
    ) Ship vertical slices — API + UI + tests per module Document continuously — READMEs,
    API examples,
    ADRs Final Thought AI accelerates the productivity.Architecture protects Use both intentionally to build fast
    and build clean.Show more Feb 17 Architected modular exam portal with vertical slices
    and clear contracts Architected modular exam portal with vertical slices
    and clear contracts 🏗 ️ Modular Scalable Architecture — Scholarship Exam Portal Your article is spot on.Let me rethink the entire architecture with vertical slices,
    contract - first design,
    and human - led module boundaries before touching any code.🧠 Architecture Thinking First The original flat structure would hit the wall fast.Here 's why the exam portal specifically needs modular thinking:

PAIN POINTS IF NOT MODULAR:
─────────────────────────────────────────────────────
1. Questions module changes break Attempt module silently
2. Analysis logic mixed with exam logic = untestable
3. Adding Hindi support requires touching 15 files
4. Admin features tangled with student features
5. AI context window explodes — unreliable suggestions
6. New exam type (8th std) requires risky refactors
📦 Vertical Slice Design — Module Map
┌─────────────────────────────────────────────────────────────────┐
│                    EXAM PORTAL — MODULE MAP                     │
├──────────────┬──────────────┬───────────────┬───────────────────┤
│   AUTH       │    USER      │    CATALOG    │   QUESTION        │
│  ─────────   │  ─────────   │  ─────────    │  ─────────        │
│  Register    │  Profile     │  Exam List    │  Question CRUD    │
│  Login/JWT   │  Preferences │  Paper Mgmt   │  Passage/Image    │
│  Roles       │  Medium/Lang │  Subject Mgmt │  Options          │
│  Refresh     │  School Info │  Topic Tags   │  Bulk Import      │
├──────────────┼──────────────┼───────────────┼───────────────────┤
│   ATTEMPT    │  ANALYSIS    │   MEDIA       │   ADMIN           │
│  ─────────   │  ─────────   │  ─────────    │  ─────────        │
│  Start Exam  │  Scoring     │  Image Upload │  Dashboard        │
│  Auto-Save   │  Topic Perf  │  PDF Storage  │  Reports          │
│  Submit      │  Time Anal.  │  CDN Serve    │  User Mgmt        │
│  Timer State │  Recommend.  │               │  Content Review   │
└──────────────┴──────────────┴───────────────┴───────────────────┘

Each module owns: routes + models + schemas + services + tests + README
Modules communicate ONLY through defined contracts — never direct imports
📋 Module ADRs (Architecture Decision Records)
ADR-001: Auth Module

Boundary:    JWT issuance, validation, refresh, role checks
Owns:        users table (auth columns only)
Exposes:     /api/auth/* routes + verify_token() dependency
Consumes:    Nothing (no dependencies on other modules)
Pattern:     Sync REST
Decision:    JWT over sessions — stateless, scales horizontally
ADR-002: User Module

Boundary:    Student/Teacher profile, preferences, language settings
Owns:        user_profiles table
Exposes:     /api/users/* routes + get_user_profile() service
Consumes:    Auth module (verify_token dependency injection)
Pattern:     Sync REST
Decision:    Separate from Auth — profile can evolve independently
ADR-003: Catalog Module

Boundary:    Exam metadata, subjects, topics, paper configuration
Owns:        exams, subjects, topics tables
Exposes:     /api/catalog/* routes + ExamService interface
Consumes:    Auth (for admin writes)
Pattern:     Sync REST (read-heavy, cacheable)
Decision:    Read-heavy → add Redis cache layer later without 
             touching other modules
ADR-004: Question Module

Boundary:    Questions, options, passages, images, bulk import
Owns:        questions, options, passages tables
Exposes:     /api/questions/* + QuestionRepository interface
Consumes:    Catalog (exam_id validation), Media (image_url)
Pattern:     Sync REST
Decision:    Questions never call Attempt — one-way dependency
ADR-005: Attempt Module

Boundary:    Exam session lifecycle (start → auto-save → submit)
Owns:        attempts, responses tables
Exposes:     /api/attempts/* + AttemptService interface
Consumes:    Catalog (exam validation), Question (fetch questions),
             Auth (user identity)
Pattern:     Sync REST + periodic auto-save
Decision:    Attempt module does NOT calculate scores — delegates to 
             Analysis via event/call boundary
ADR-006: Analysis Module

Boundary:    Scoring, topic performance, time analysis, recommendations
Owns:        No tables — reads from attempts/responses (read-only access)
Exposes:     /api/analysis/* + AnalysisService interface
Consumes:    Attempt (read-only), Question (topic mapping)
Pattern:     Sync REST (compute-heavy → async queue later)
Decision:    Pure computation — no side effects, fully testable
ADR-007: Media Module

Boundary:    File upload, image serving, PDF generation
Owns:        media_files table
Exposes:     /api/media/* + MediaService interface
Consumes:    Auth (upload permissions)
Pattern:     Sync REST
Decision:    Cloudinary in prod, local filesystem in dev —
             swappable via interface
ADR-008: Admin Module

Boundary:    Admin-only operations aggregating other modules
Owns:        No tables — orchestrates other modules
Exposes:     /api/admin/* routes
Consumes:    All modules through their public interfaces
Pattern:     Sync REST (admin actions are rare, low volume)
Decision:    Admin is an orchestrator — never adds business logic
🗂️ Scalable Project Structure
/scholarship-exam-portal
│
├── /backend
│   ├── /app
│   │   ├── main.py                    # App factory, middleware, router mounts
│   │   ├── config.py                  # Settings via pydantic-settings
│   │   ├── database.py                # DB connection, session factory
│   │   ├── dependencies.py            # Shared FastAPI dependencies
│   │   │
│   │   ├── /modules                   # ← VERTICAL SLICES
│   │   │   │
│   │   │   ├── /auth
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py          # /api/auth/* endpoints
│   │   │   │   ├── models.py          # SQLAlchemy: User (auth cols)
│   │   │   │   ├── schemas.py         # Pydantic: LoginRequest, TokenResponse
│   │   │   │   ├── service.py         # AuthService: login, register, refresh
│   │   │   │   ├── dependencies.py    # verify_token, require_role
│   │   │   │   ├── exceptions.py      # AuthException, InvalidTokenError
│   │   │   │   ├── README.md          # Module contract + usage
│   │   │   │   └── /tests
│   │   │   │       ├── test_router.py
│   │   │   │       └── test_service.py
│   │   │   │
│   │   │   ├── /user
│   │   │   │   ├── router.py
│   │   │   │   ├── models.py          # UserProfile
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py         # UserService
│   │   │   │   ├── README.md
│   │   │   │   └── /tests
│   │   │   │
│   │   │   ├── /catalog
│   │   │   │   ├── router.py
│   │   │   │   ├── models.py          # Exam, Subject, Topic
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py         # CatalogService (public interface)
│   │   │   │   ├── README.md
│   │   │   │   └── /tests
│   │   │   │
│   │   │   ├── /question
│   │   │   │   ├── router.py
│   │   │   │   ├── models.py          # Question, Option, Passage
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py         # QuestionService (public interface)
│   │   │   │   ├── repository.py      # DB queries isolated here
│   │   │   │   ├── importer.py        # Bulk JSON/CSV import logic
│   │   │   │   ├── README.md
│   │   │   │   └── /tests
│   │   │   │
│   │   │   ├── /attempt
│   │   │   │   ├── router.py
│   │   │   │   ├── models.py          # Attempt, Response
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py         # AttemptService (public interface)
│   │   │   │   ├── state_machine.py   # not_started→ongoing→submitted
│   │   │   │   ├── README.md
│   │   │   │   └── /tests
│   │   │   │
│   │   │   ├── /analysis
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py         # ReportSchema, TopicPerformance
│   │   │   │   ├── service.py         # AnalysisService (pure computation)
│   │   │   │   ├── scorer.py          # Scoring logic (isolated + testable)
│   │   │   │   ├── recommender.py     # Recommendation engine
│   │   │   │   ├── README.md
│   │   │   │   └── /tests
│   │   │   │       ├── test_scorer.py       # unit tests, no DB needed
│   │   │   │       └── test_recommender.py
│   │   │   │
│   │   │   ├── /media
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py
│   │   │   │   ├── service.py         # MediaService interface
│   │   │   │   ├── /providers
│   │   │   │   │   ├── base.py        # Abstract MediaProvider
│   │   │   │   │   ├── cloudinary.py  # Prod provider
│   │   │   │   │   └── local.py       # Dev provider
│   │   │   │   └── README.md
│   │   │   │
│   │   │   └── /admin
│   │   │       ├── router.py          # Orchestrates other modules
│   │   │       ├── schemas.py
│   │   │       └── README.md
│   │   │
│   │   └── /shared                    # Shared utilities (NO business logic)
│   │       ├── pagination.py
│   │       ├── exceptions.py          # Base exception classes
│   │       ├── i18n.py                # Language resolution helper
│   │       └── logging.py
│   │
│   ├── /migrations                    # Alembic migrations
│   ├── /tests
│   │   ├── conftest.py                # Shared fixtures
│   │   └── /integration               # Cross-module integration tests
│   ├── /docs
│   │   ├── /adr                       # ADR-001 through ADR-008
│   │   └── openapi_extended.yaml      # Extended API contracts
│   ├── seed.py
│   ├── requirements.txt
│   └── .env.example
│
├── /frontend
│   ├── /src
│   │   ├── /modules                   # ← MIRRORS BACKEND SLICES
│   │   │   ├── /auth
│   │   │   │   ├── /api               # authApi.js (axios calls)
│   │   │   │   ├── /components        # LoginForm, RegisterForm
│   │   │   │   ├── /pages             # LoginPage, RegisterPage
│   │   │   │   ├── /store             # authStore.js (Zustand slice)
│   │   │   │   └── index.js           # Public exports only
│   │   │   │
│   │   │   ├── /exam                  # Catalog + Question display
│   │   │   │   ├── /api
│   │   │   │   ├── /components        # ExamCard, PaperList
│   │   │   │   ├── /pages             # ExamListPage
│   │   │   │   └── index.js
│   │   │   │
│   │   │   ├── /attempt               # Exam-taking interface
│   │   │   │   ├── /api
│   │   │   │   ├── /components
│   │   │   │   │   ├── ExamShell.jsx        # Main layout
│   │   │   │   │   ├── QuestionCard.jsx     # Single question renderer
│   │   │   │   │   ├── QuestionPalette.jsx  # Number grid sidebar
│   │   │   │   │   ├── CountdownTimer.jsx   # Timer component
│   │   │   │   │   └── SubmitDialog.jsx     # Confirm modal
│   │   │   │   ├── /hooks
│   │   │   │   │   ├── useExamTimer.js
│   │   │   │   │   └── useAutoSave.js
│   │   │   │   ├── /store             # attemptStore.js
│   │   │   │   ├── /pages             # ExamPage
│   │   │   │   └── index.js
│   │   │   │
│   │   │   ├── /analysis
│   │   │   │   ├── /api
│   │   │   │   ├── /components
│   │   │   │   │   ├── ScoreCard.jsx
│   │   │   │   │   ├── SubjectBreakdown.jsx
│   │   │   │   │   ├── TopicPerformance.jsx
│   │   │   │   │   ├── QuestionReview.jsx
│   │   │   │   │   ├── TimeAnalysis.jsx
│   │   │   │   │   └── Recommendations.jsx
│   │   │   │   ├── /pages             # ResultPage
│   │   │   │   └── index.js
│   │   │   │
│   │   │   ├── /admin
│   │   │   │   ├── /components
│   │   │   │   ├── /pages
│   │   │   │   └── index.js
│   │   │   │
│   │   │   └── /dashboard
│   │   │       ├── /components
│   │   │       └── /pages
│   │   │
│   │   ├── /shared                    # Shared UI only
│   │   │   ├── /components            # Button, Modal, Spinner, Badge
│   │   │   ├── /layouts               # AppLayout, ExamLayout
│   │   │   ├── /hooks                 # useLanguage, useMediaQuery
│   │   │   └── /i18n                  # Language files
│   │   │       ├── /en
│   │   │       ├── /mr
│   │   │       └── /hi
│   │   │
│   │   ├── /router                    # Route definitions
│   │   ├── /config                    # API base URL, constants
│   │   └── App.jsx
│   │
│   └── package.json
│
├── /docs
│   ├── ARCHITECTURE.md
│   ├── MODULE_CONTRACTS.md
│   └── /adr
│
└── docker-compose.yml
📝 The Revised Claude Code Prompt
# SCHOLARSHIP EXAM PORTAL — MODULAR IMPLEMENTATION

## CORE PRINCIPLE
Build this as VERTICAL SLICES. Each module is self-contained with its own
routes, models, schemas, service, and tests. Modules communicate ONLY through
their public service interfaces — never import internal module files directly.

AI handles: scaffolding, boilerplate, tests, DTOs, validation
Human-designed (already decided): architecture, module boundaries, 
                                   data ownership, communication patterns

---

## PROJECT: ScholarPath — MSCE Maharashtra Scholarship Exam Portal
## EXAM STRUCTURE:
- 5th Standard (Pre-Upper Primary) and 8th Standard (Pre-Secondary)
- Paper 1 (0501): Section I = First Language Q1-25 | Section II = Math Q26-75
- Paper 2 (0502): Section I = Third Language Marathi Q1-25 | Section II = Intelligence Test Q26-75
- 75 questions × 2 marks = 150 marks | 90 minutes | MCQ 4 options
- Languages: English, Marathi, Hindi, Semi-English

---

## TECH STACK (free/open-source):
Backend:  Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic + pydantic-settings
Database: PostgreSQL (SQLite for local dev via DATABASE_URL env)
Auth:     JWT (python-jose + passlib bcrypt)
Frontend: React 18 + Vite + Tailwind CSS 3 + Zustand + react-i18next + Recharts
HTTP:     Axios with interceptors
PDF:      jsPDF + html2canvas
Deploy:   Vercel (FE) + Render (BE) + Supabase (DB prod)

---

## MODULE CONTRACTS (implement these exactly):

### MODULE 1: AUTH
File: /backend/app/modules/auth/
Contract:
  Public interface: AuthService.register(), AuthService.login(), 
                    AuthService.refresh_token()
  FastAPI dependency: verify_token(token) → UserIdentity
  FastAPI dependency: require_role(role) → decorator
  Routes: POST /api/auth/register, /api/auth/login, /api/auth/refresh
  Owns DB: users table (id, email, password_hash, role, is_active, created_at)
  Consumes: Nothing
  
  Schemas (Pydantic):
    RegisterRequest: name, email, password, std_class(5|8), 
                     medium(english|marathi|hindi|semi_english), 
                     school_name, district
    LoginRequest: email, password
    TokenResponse: access_token, refresh_token, token_type, expires_in
    UserIdentity: id, email, role, std_class, medium (decoded from JWT)
  
  Rules: 
    - Password: min 8 chars, bcrypt hash
    - JWT access token: 30 min expiry
    - JWT refresh token: 7 days
    - Roles: student | admin | teacher

### MODULE 2: USER
File: /backend/app/modules/user/
Contract:
  Public interface: UserService.get_profile(user_id), 
                    UserService.update_profile(user_id, data)
  Routes: GET/PUT /api/users/me, GET /api/users/{user_id} (admin only)
  Owns DB: user_profiles table (user_id FK, name, school_name, district, 
                                 std_class, medium, avatar_url, created_at)
  Consumes: Auth module (verify_token dependency)
  
  Note: user_profiles.user_id references auth.users.id
        User module never imports from auth module internals —
        only uses the verify_token dependency from auth/dependencies.py

### MODULE 3: CATALOG
File: /backend/app/modules/catalog/
Contract:
  Public interface: CatalogService.get_exam(exam_id), 
                    CatalogService.list_exams(std_class, year),
                    CatalogService.get_subjects(exam_id)
  Routes: GET /api/catalog/exams, GET /api/catalog/exams/{id},
          GET /api/catalog/exams/{id}/subjects
          POST/PUT/DELETE /api/catalog/* (admin role required)
  Owns DB: 
    exams(id, title_en, title_mr, paper_code, std_class, year, 
          total_marks, duration_minutes, is_active, created_at)
    subjects(id, exam_id, name_en, name_mr, name_hi, 
             question_from, question_to, order_index)
    topics(id, subject_id, name_en, name_mr, name_hi, 
           question_ids JSON array)
  Consumes: Auth (admin role check only)
  
  Scaling note: This module is read-heavy. 
  Add @cache decorator on list_exams() and get_exam() — 
  cache key includes std_class+year. Easy to add Redis later.

### MODULE 4: QUESTION
File: /backend/app/modules/question/
Contract:
  Public interface: QuestionService.get_questions_for_exam(exam_id, language),
                    QuestionService.get_question(question_id),
                    QuestionService.validate_answer(question_id, selected_option)
  Routes: GET /api/questions/exam/{exam_id} (requires active attempt),
          POST /api/questions (admin), POST /api/questions/bulk-import (admin)
  Owns DB:
    questions(id, exam_id, subject_id, topic_id, question_no, 
              text_en, text_mr, text_hi,
              question_type ENUM(text|image|passage|bilingual),
              image_url, passage_id, marks, correct_option, 
              explanation_en, explanation_mr, difficulty ENUM(easy|medium|hard),
              created_at)
    options(id, question_id, option_no INT 1-4, 
            text_en, text_mr, text_hi, image_url)
    passages(id, exam_id, text_en, text_mr, text_hi, 
             question_from, question_to)
  Consumes: Catalog (exam_id validation), Media (image_url storage)
  
  Rule: Question module NEVER returns correct_option to frontend 
        during exam — only returns it in admin routes and analysis.
  
  Bulk import JSON format:
  {
    "exam_id": 1,
    "questions": [{
      "question_no": 1,
      "text_en": "...", "text_mr": "...",
      "type": "text",
      "correct_option": 2,
      "explanation_en": "...",
      "options": [
        {"option_no": 1, "text_en": "Chess", "text_mr": "बुद्धिबळ"},
        {"option_no": 2, "text_en": "Tennis", "text_mr": "टेनिस"}
      ]
    }]
  }

### MODULE 5: ATTEMPT
File: /backend/app/modules/attempt/
Contract:
  Public interface: AttemptService.start(user_id, exam_id),
                    AttemptService.save_response(attempt_id, question_id, option),
                    AttemptService.submit(attempt_id)
  Routes: POST /api/attempts/start, 
          POST /api/attempts/{id}/responses (auto-save single response),
          POST /api/attempts/{id}/submit,
          GET  /api/attempts/{id}/state (resume exam — returns saved answers),
          GET  /api/attempts/history (user' s past attempts
) Owns DB: attempts(
    id,
    user_id,
    exam_id,
    status ENUM(ongoing | submitted | expired),
    started_at,
    submitted_at,
    auto_save_at,
    ip_address
) responses(
    id,
    attempt_id,
    question_id,
    selected_option INT nullable,
    answered_at,
    time_taken_seconds INT
) Consumes: Catalog (exam validation),
Question (question validation),
Auth (user identity) State machine (implement as state_machine.py): not_started → ongoing (on start) ongoing → submitted (
    on submit
    or timer expiry
) ongoing → expired (
    if restarted
    after 90min without submit
) Rules: - One active attempt per user per exam at a time - Auto - save: POST / api / attempts / { id } / responses accepts single response,
called by frontend every time student selects an option - Submit validates: attempt belongs to current user,
status is ongoing -
After submit,
    attempt status = submitted (immutable) - IMPORTANT: Attempt module does NOT calculate scores.It only stores raw responses.Score calculation = Analysis module 's job.

### MODULE 6: ANALYSIS  
File: /backend/app/modules/analysis/
Contract:
  Public interface: AnalysisService.generate_report(attempt_id),
                    AnalysisService.get_user_performance(user_id)
  Routes: GET /api/analysis/attempts/{attempt_id}/report,
          GET /api/analysis/users/me/performance,
          GET /api/analysis/exams/{exam_id}/leaderboard
  Owns DB: No tables. Read-only access to attempts and responses 
           via repository pattern.
  Consumes: Attempt (read-only), Question (for correct answers + topics)
  
  Report schema to generate:
  {
    "attempt_id": 1,
    "exam_title": {"en": "...", "mr": "..."},
    "score": {"obtained": 118, "total": 150, "percentage": 78.6},
    "grade": "Good",  // Excellent≥90%, Good≥70%, Average≥50%, Below Average<50%
    "subject_breakdown": [
      {"subject": "English", "obtained": 38, "total": 50, "percentage": 76}
    ],
    "topic_performance": [
      {"topic": "Grammar", "obtained": 16, "total": 20, 
       "percentage": 80, "status": "strong|average|weak"}
    ],
    "time_analysis": {
      "total_seconds": 3240,
      "avg_per_question": 72,
      "fastest_question": {"no": 3, "seconds": 15},
      "slowest_question": {"no": 47, "seconds": 220}
    },
    "question_review": [
      {"question_no": 12, "text_en": "...", "text_mr": "...",
       "selected_option": 1, "correct_option": 4,
       "is_correct": false, "explanation_en": "..."}
    ],
    "recommendations": [
      "Practice more Fraction problems — you scored 40% in this topic",
      "You' re strong in Intelligence Test — keep it up ! "
    ],
    " stats ": {
      " correct ": 59, " wrong ": 12, " skipped ": 4
    }
  }
  
  Scorer (scorer.py — pure functions, no DB, fully unit-testable):
    calculate_score(responses, questions) → ScoreResult
    calculate_topic_performance(responses, questions, topics) → List[TopicResult]
    calculate_time_analysis(responses) → TimeResult
    generate_grade(percentage) → str
    
  Recommender (recommender.py — pure functions):
    generate_recommendations(topic_performance) → List[str]
    Threshold: topic < 50% → " weak " → generate specific recommendation

### MODULE 7: MEDIA
File: /backend/app/modules/media/
Contract:
  Public interface: MediaService.upload(file, folder) → url,
                    MediaService.delete(file_id)
  Routes: POST /api/media/upload (admin only)
  Provider pattern (base.py abstract class):
    class MediaProvider(ABC):
      def upload(self, file: bytes, filename: str, folder: str) -> str
      def delete(self, file_id: str) -> bool
  Providers:
    LocalProvider: saves to /uploads, serves via /static (development)
    CloudinaryProvider: uses Cloudinary API (production)
  Selection: via MEDIA_PROVIDER env var = " local " | " cloudinary "
  
  Note: This design means dev uses local files, 
  prod uses Cloudinary — zero code changes, just env var.

### MODULE 8: ADMIN
File: /backend/app/modules/admin/
Contract:
  This module is an ORCHESTRATOR only — no business logic.
  Routes: GET /api/admin/dashboard (stats aggregation),
          GET /api/admin/students (paginated list),
          GET /api/admin/reports (all attempt reports),
          POST /api/admin/questions/bulk-import (delegates to Question module)
  Consumes: All modules through their public interfaces only.
  Rule: If admin needs new logic, add it to the owning module, 
        not here. Admin only aggregates and delegates.

---

## CROSS-CUTTING CONCERNS (implement in /shared and main.py):

### Error Handling (shared/exceptions.py):
Base exceptions:
  AppException(status_code, error_code, message_en, message_mr)
Module exceptions inherit from AppException:
  AuthException, QuestionNotFoundException, AttemptAlreadySubmittedException, etc.
Global exception handler in main.py returns:
  {" error ": {" code ": " ATTEMPT_ALREADY_SUBMITTED ", 
             " message ": " Exam already submitted "}}

### Language Resolution (shared/i18n.py):
  def get_text(obj, lang: str) -> str:
    # Returns obj.text_en, obj.text_mr, or obj.text_hi based on lang
    # Falls back to English if requested language is null
  Used by all modules — never duplicated.

### Pagination (shared/pagination.py):
  class PaginatedResponse(Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
  All list endpoints use this.

### Logging (shared/logging.py):
  Structured JSON logs with: module, action, user_id, duration_ms
  Format: {" module ": " attempt ", " action ": " submit ", 
           " user_id ": 42, " duration_ms ": 145}

---

## FRONTEND MODULE RULES:

Each frontend module exports ONLY through its index.js:
  // /modules/auth/index.js
  export { LoginPage } from './pages/LoginPage'
  export { RegisterPage } from './pages/RegisterPage'  
  export { useAuthStore } from './store/authStore'
  // Nothing else is importable from outside this module

Module communication via Zustand stores only:
  authStore: { user, token, login(), logout() }
  attemptStore: { currentAttempt, responses, saveResponse(), 
                  timer, questionStatus }
  analysisStore: { report, loading, fetchReport() }

Axios instance (config/apiClient.js):
  - Base URL from VITE_API_URL env var
  - Request interceptor: attach JWT token
  - Response interceptor: handle 401 → auto-logout, 
                          handle network errors globally
  - Each module has its own api file using this shared client

---

## IMPLEMENTATION ORDER (one module at a time):

PHASE 1 — Foundation:
  1. Backend: Setup FastAPI app factory, database, shared utilities
  2. Backend: Auth module (complete with tests)
  3. Backend: User module (complete with tests)
  4. Frontend: Project setup (Vite + Tailwind + i18n + Zustand)
  5. Frontend: Auth module (Login + Register pages)
  
PHASE 2 — Content:
  6. Backend: Catalog module + seed data
  7. Backend: Question module + bulk import + seed 10 questions
  8. Frontend: Dashboard page
  9. Frontend: Exam list (Catalog module frontend)
  
PHASE 3 — Core Exam Flow:
  10. Backend: Attempt module (state machine, auto-save, submit)
  11. Frontend: Attempt module (ExamShell, QuestionCard, 
                Timer, Palette, Auto-save)
  
PHASE 4 — Analysis:
  12. Backend: Analysis module (scorer.py + recommender.py with full unit tests)
  13. Frontend: Analysis module (ScoreCard, TopicPerformance, 
                QuestionReview, Recommendations, PDF export)
  
PHASE 5 — Polish:
  14. Media module
  15. Admin module + bulk question import
  16. i18n completion (all strings in EN/MR/HI)
  17. Responsive design + mobile exam interface
  18. Deployment configs

---

## SEED DATA:
Create seed.py that populates:
1. Admin user: admin@scholarpath.in / Admin@123
2. Student user: student@test.in / Student@123 (std_class=5, medium=english)
3. One complete exam: " Pre - Upper Primary Scholarship 2025 - Paper 1 "
   with 15 sample questions covering all types:
   
   Q1-Q2: Passage MCQ (Bal Gandharva passage)
   Q3-Q5: Poem MCQ (The House Next Door)  
   Q6: Grammar MCQ bilingual
     text_en: " There are twelve months in a year.August is ________ month."
     text_mr: " वर्षात बारा महिने असतात.ऑगस्ट हा ________ महिना आहे."
     options: eighth, eight, seventh, seven | correct: 1
   Q7: Greeting MCQ
   Q26: Math - Weight addition
   Q34: Math - Simple Interest
   Q46: Math - Perimeter/Area
   Intelligence Test sample:
     text_en: " Which game requires a racket for playing it ? "
     text_mr: " कोणता खेळ खेळण्याकरिता रॅकेटची गरज असते ? "
     options_en: Chess, Cricket, Hockey, Tennis
     options_mr: बुद्धिबळ, क्रिकेट, हॉकी, टेनिस
     correct: 4

---

## TESTS TO WRITE:
For each module, write tests in this order:
1. Unit tests for service/pure functions (no DB)
2. Integration tests for routes (with test DB)
3. Contract tests: verify module's public interface matches schema

Priority tests (write these first, they protect module boundaries):
- test_auth: register → login → get JWT → verify JWT
- test_attempt_state_machine: all valid/invalid transitions
- test_scorer: calculate_score() with known responses (pure function)
- test_recommender: generate_recommendations() for weak/strong topics
- test_question: correct_option NOT exposed in exam fetch endpoint

---

## ENVIRONMENT VARIABLES (.env.example):
# Backend
DATABASE_URL=postgresql://user:pass@localhost/scholarpath
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
MEDIA_PROVIDER=local  # or cloudinary
CLOUDINARY_URL=cloudinary://...  # only if provider=cloudinary

# Frontend  
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=ScholarPath
VITE_DEFAULT_LANGUAGE=en

---

## WHAT NOT TO DO (guardrails):
- Never import across module internals: 
  ✅ from app.modules.auth.dependencies import verify_token
  ❌ from app.modules.auth.models import User  (from another module)
- Never put business logic in routers — routers call services only
- Never put DB queries in routers or services — use repository pattern
- Analysis module never writes to DB — read-only always
- Question module never returns correct_option during active exam
- Admin module never contains business logic — delegates only
- Frontend modules never import from another module's internal files

Build Phase 1 first. Confirm structure before proceeding to Phase 2.
🔑 Key Scalability Wins This Gives You
The modular boundary approach means you can later:

Add Redis caching to Catalog module only — zero other files touched
Make Analysis async (Celery queue) — only Analysis module changes
Add Hindi support — only shared/i18n.py + translation files
New exam type (8th std) — just add a new Catalog entry + Questions
Mobile app later — backend API contracts unchanged, only new frontend consumer
Microservices later — each module is already designed to be independently extractable
The AI handles the scaffolding inside each module. The boundaries above are yours to protect.

Want me to start building Phase 1 now — the FastAPI app factory + Auth module with full tests?

this is good approch. 
what i am thinking is below i have return few of the things how we can approch the website . we need data base and the questions ready in the data base. We need api to call this exam. on the basis of that DB we can build the proper structure on the website. Instade of groing from UI i think we need a strcutred data base first.  then we can go ahade and work on other things. 
With the given prompt below which i just wrote down what do you think the DB strcutre should be ?

2:12 PM
CCC_0501_V_English_P_1_25_A.pdf
pdf

CCC_0502_V_English_II_25_A.pdf
pdf

this is good approch. 
what i am thinking is below i have return few of the things how we can approch the website . we need data base and the questions ready in the data base. We need api to call this exam. on the basis of that DB we can build the proper structure on the website. Instade of groing from UI i think we need a strcutred data base first.  then we can go ahade and work on other things. 
With the given prompt below which i just wrote down what do you think the DB strcutre should be ?
1. Question Bank for the Exam
* 
1. 
1. Create different question bank.
2. Create exam bank.
3. Maintain the avarage correct and wrong questions attempts 
* 
1. Login system
* 
1. 
1. Give google or face book or personal login.
* 
1. Data storate for the exam
* 
1. 
1. Finilize the data strcture .
2. Build the backend system for the data retrive and push
* 
1. Exam Taking engin .
* 
1. 
1. Assign the exam for the student.
2. Set the timer for the exam so that it should work accordingly.
3. Store the exam and give the statistic of the exam to the student.
* 
1. Assign exam for the student.
* 
1. 
1. Need to think
* 
1. Select multiple exams
* 
1. 
1. You should have assigned multiple exams to students.
2. Student can take multiple to practice.
* 
1. Parent dash board.
* 
1. 
1. Should see what student is don’t.
2. How they are performing.
3. There attempt and how they are doing with the exam.
4. Should show what is missing and help to focus on the missing parts.
* 
1. Admin dashboard.
* 
1. 
1. Give the admin panel
* 
1. 
1. 
1. Admin panel should show how many students logged in.
2. How many did enquiries.
3. Support information
4. Questions.
5. How many test taken
* 
1. 
1. Reporting basically
* 
1. 
1. 
1. We will cover the student register
2. The exams taken
3. Traffic of the students
4. Analytics
* 
1. Exam Admin panel
* 
1. 
1. Now this one will help to assign the exams to kids.
2. Save questions
3. Save the questions information
* 
1. 
1. 
1. What type of question
2. What category and the level of hard ness.
3. Image and the exam info.
* 
1. 
1. The exam question can be stored as the Json as we have limited question set.
* 
1. 
1. 
1. But we need to think on that.
* 
1. 
1. Exam and associated question rule.
2. Exam Creation engine.
* 
1. 
1. 
1. This is hard we need to think on that we will work on that. Slowly. 
think and come up with best possible version to develop the data base so i can start creating the data table in the 
Supabase . i am attaching the example questions pdf also for you to understand the structure and work accordingly

Show more
2:19 PM

Architected comprehensive database schema for exam platform
Architected comprehensive database schema for exam platform
















📊 Database Structure — Designed from the Actual PDFs + Your Requirements
Looking at both PDFs carefully, I can see things the generic design missed. Let me call them out first.

🔍 What the PDFs Revealed About Data Complexity
PAPER 0501 QUESTION TYPES FOUND:
─────────────────────────────────────────────
Q1-2   → Paragraph passage → 2 questions share one context
Q3-5   → Poem passage      → 3 questions share one context  
Q9-11  → Advertisement     → Image + text context
Q24-25 → Picture (flag)    → Image-only context
Q35-36 → Pictograph table  → Data table as context
Q33    → Counting triangles in figure → image in question
Q41    → Shaded fraction figure → image in question

PAPER 0502 INTELLIGENCE TEST:
─────────────────────────────────────────────
Q27-28 → Mirror image  → BOTH question AND options are images
Q29-30 → Water image   → BOTH question AND options are images
Q32-37 → Figure series → images in question + options
Q43    → Venn diagram  → image as context
Q48    → Shape pattern → all options are images
Q63-64 → Odd figure   → all options are images

MARATHI SECTION (Q1-25 in 0502):
─────────────────────────────────────────────
Q14-16 → Marathi passage (nature paragraph)
Q17-19 → Marathi poem (पानांचे गाणे)
→ Questions exist in MARATHI ONLY (no English translation)
This is critical — some questions are purely Marathi, some are bilingual, some are image-only with no text at all. The DB must handle all these gracefully.

🏗️ Final Database Design for Supabase
Layer 1 — Exam Catalog (What exams exist)
sql
-- EXAM EVENTS: Groups Paper I and Paper II together
-- e.g. " MSCE 5th Std Scholarship Feb 2025 " is one event
CREATE TABLE exam_events (
    id          SERIAL PRIMARY KEY,
    title_en    TEXT NOT NULL,
    title_mr    TEXT,
    std_class   SMALLINT NOT NULL,         -- 5 or 8
    year        SMALLINT NOT NULL,
    exam_date   DATE,
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- EXAMS: Each paper is one exam (501, 502)
CREATE TABLE exams (
    id                  SERIAL PRIMARY KEY,
    event_id            INT REFERENCES exam_events(id),
    paper_code          VARCHAR(10) NOT NULL,    -- '501', '502'
    set_code            VARCHAR(5) DEFAULT 'A',  -- A, B, C, D
    title_en            TEXT NOT NULL,
    title_mr            TEXT,
    paper_number        SMALLINT,                -- 1 or 2
    medium              VARCHAR(20) DEFAULT 'english', 
    total_questions     SMALLINT DEFAULT 75,
    total_marks         SMALLINT DEFAULT 150,
    marks_per_question  SMALLINT DEFAULT 2,
    duration_minutes    SMALLINT DEFAULT 90,
    is_active           BOOLEAN DEFAULT false,   -- admin publishes manually
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
-- Index: paper_code + set_code for fast lookup

-- SECTIONS: Each exam has sections (Section I and Section II)
CREATE TABLE sections (
    id              SERIAL PRIMARY KEY,
    exam_id         INT REFERENCES exams(id) ON DELETE CASCADE,
    section_label   VARCHAR(5) NOT NULL,     -- 'I', 'II'
    subject_en      TEXT NOT NULL,           -- 'English', 'Mathematics', 'Intelligence Test'
    subject_mr      TEXT,
    question_from   SMALLINT NOT NULL,       -- 1
    question_to     SMALLINT NOT NULL,       -- 25
    order_index     SMALLINT DEFAULT 1
);

-- TOPICS: Sub-categories for analysis (e.g. Grammar, Fractions, Mirror Images)
CREATE TABLE topics (
    id          SERIAL PRIMARY KEY,
    section_id  INT REFERENCES sections(id) ON DELETE CASCADE,
    name_en     TEXT NOT NULL,
    name_mr     TEXT,
    description TEXT
);
Layer 2 — Question Bank (The core content)
sql
-- QUESTION CONTEXTS: Passages, poems, ads, instructions, images
-- A context can apply to a GROUP of questions (Q1-2 share one passage)
CREATE TABLE question_contexts (
    id              SERIAL PRIMARY KEY,
    exam_id         INT REFERENCES exams(id) ON DELETE CASCADE,
    
    context_type    VARCHAR(30) NOT NULL,
    -- Values: 'paragraph', 'poem', 'advertisement', 'image', 
    --         'pictograph', 'instruction', 'venn_diagram', 
    --         'figure_series', 'table'
    
    title_en        TEXT,           -- e.g. " The House Next Door "
    title_mr        TEXT,
    
    content_en      TEXT,           -- Full passage/poem text in English
    content_mr      TEXT,           -- Full passage/poem text in Marathi
    
    image_url       TEXT,           -- For image/pictograph/figure contexts
    
    -- For Intelligence Test: " Q.27
    and Q.28 Direction:
Select the mirror image..."
    instruction_en  TEXT,
    instruction_mr  TEXT,
    
    -- Which questions this context applies to
    applies_from    SMALLINT,       -- 1
    applies_to      SMALLINT,       -- 5  (means Q1 to Q5 use this context)
    
    order_index     SMALLINT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- QUESTIONS: The main question table
CREATE TABLE questions (
    id              SERIAL PRIMARY KEY,
    exam_id         INT REFERENCES exams(id) ON DELETE CASCADE,
    section_id      INT REFERENCES sections(id),
    topic_id        INT REFERENCES topics(id),
    context_id      INT REFERENCES question_contexts(id), -- nullable
    
    question_no     SMALLINT NOT NULL,      -- 1 to 75
    
    -- Text content (nullable for image-only questions)
    text_en         TEXT,
    text_mr         TEXT,
    
    -- Question type drives UI rendering
    question_type   VARCHAR(30) NOT NULL DEFAULT 'text',
    -- Values: 'text'         → pure text question + text options
    --         'text_image'   → text question + image in question  
    --         'image_only'   → image is the question (Intelligence Test)
    --         'context_text' → comes from passage/poem (text)
    --         'context_image'→ comes from pictograph/figure
    --         'marathi_only' → no English version exists
    --         'bilingual'    → shown in EN + MR simultaneously
    
    -- For image questions (e.g. the flag picture, shaded fraction)
    question_image_url  TEXT,
    
    marks           SMALLINT DEFAULT 2,
    correct_option  SMALLINT NOT NULL,      -- 1, 2, 3, or 4
    
    explanation_en  TEXT,
    explanation_mr  TEXT,
    
    difficulty      VARCHAR(10) DEFAULT 'medium', -- easy, medium, hard
    
    -- For admin filtering and future AI tagging
    tags            TEXT[],                 -- ['ordinal_numbers', 'grammar']
    
    -- Statistics cache (updated via trigger after each attempt)
    attempt_count   INT DEFAULT 0,
    correct_count   INT DEFAULT 0,
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(exam_id, question_no)            -- No duplicate Q numbers in same exam
);

-- OPTIONS: 4 options per question
-- Handles text options, image options, or both (Intelligence Test)
CREATE TABLE options (
    id          SERIAL PRIMARY KEY,
    question_id INT REFERENCES questions(id) ON DELETE CASCADE,
    option_no   SMALLINT NOT NULL,     -- 1, 2, 3, 4
    text_en     TEXT,                  -- null if image-only option
    text_mr     TEXT,
    image_url   TEXT,                  -- null if text-only option
    -- Both text and image can exist (bilingual option with illustration)
    UNIQUE(question_id, option_no)
);
Layer 3 — Users & Auth
sql
-- Supabase handles auth.users automatically
-- We extend it with profiles

CREATE TABLE user_profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    role        VARCHAR(20) NOT NULL DEFAULT 'student',
    -- Values: 'student', 'parent', 'teacher', 'exam_admin', 'super_admin'
    
    -- Student-specific
    std_class   SMALLINT,             -- 5 or 8
    medium      VARCHAR(20),          -- english, marathi, hindi, semi_english
    school_name TEXT,
    district    TEXT,
    
    -- For parent-child linking
    parent_id   UUID REFERENCES user_profiles(id),
    -- A parent can have multiple children via this FK
    
    avatar_url  TEXT,
    phone       TEXT,
    
    -- Onboarding status
    is_onboarded    BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Parent-Child linking (one parent → many students)
CREATE TABLE parent_student_links (
    id          SERIAL PRIMARY KEY,
    parent_id   UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    student_id  UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    linked_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(parent_id, student_id)
);
Layer 4 — Exam Assignment & Attempts
sql
-- EXAM ASSIGNMENTS: Admin assigns exam to students
-- A student can also self-assign (for practice mode)
CREATE TABLE exam_assignments (
    id              SERIAL PRIMARY KEY,
    exam_id         INT REFERENCES exams(id),
    student_id      UUID REFERENCES user_profiles(id),
    assigned_by     UUID REFERENCES user_profiles(id),  -- admin who assigned
    
    assignment_type VARCHAR(20) DEFAULT 'practice',
    -- Values: 'practice' (student self-starts), 'assigned' (by admin)
    
    max_attempts    SMALLINT DEFAULT 5,     -- how many times can retake
    valid_from      TIMESTAMPTZ,            -- null = immediately
    valid_until     TIMESTAMPTZ,            -- null = no expiry
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(exam_id, student_id)             -- one assignment per student per exam
);

-- ATTEMPTS: One attempt = one exam session
CREATE TABLE attempts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID REFERENCES user_profiles(id),
    exam_id         INT REFERENCES exams(id),
    assignment_id   INT REFERENCES exam_assignments(id),
    
    attempt_number  SMALLINT DEFAULT 1,     -- 1st, 2nd, 3rd attempt
    
    status          VARCHAR(20) DEFAULT 'ongoing',
    -- Values: 'ongoing', 'submitted', 'expired', 'abandoned'
    
    -- Timestamps
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    submitted_at    TIMESTAMPTZ,
    last_saved_at   TIMESTAMPTZ DEFAULT NOW(),
    
    -- Results (populated on submit)
    total_score         SMALLINT,
    total_correct       SMALLINT,
    total_wrong         SMALLINT,
    total_skipped       SMALLINT,
    percentage          NUMERIC(5,2),
    duration_seconds    INT,
    
    -- Section-wise scores (JSON for flexibility)
    section_scores  JSONB,
    -- Example: {" section_I ": {" score ": 38, " total ": 50}, 
    --           " section_II ": {" score ": 80, " total ": 100}}
    
    -- Topic-wise scores (JSON, computed on submit)
    topic_scores    JSONB,
    -- Example: [{" topic_id ": 1, " name ": " Grammar ", 
    --            " correct ": 4, " total ": 5, " status ": " strong "}]
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- RESPONSES: One row per question answered
CREATE TABLE responses (
    id              BIGSERIAL PRIMARY KEY,
    attempt_id      UUID REFERENCES attempts(id) ON DELETE CASCADE,
    question_id     INT REFERENCES questions(id),
    question_no     SMALLINT NOT NULL,          -- denormalized for speed
    
    selected_option SMALLINT,                   -- null = skipped/not visited
    is_correct      BOOLEAN,
    marks_obtained  SMALLINT DEFAULT 0,
    
    -- Time tracking
    answered_at         TIMESTAMPTZ,
    time_taken_seconds  SMALLINT,
    
    -- Exam palette state (for resume)
    visit_count     SMALLINT DEFAULT 0,         -- how many times visited
    is_marked_review BOOLEAN DEFAULT false,      -- marked for review flag
    
    UNIQUE(attempt_id, question_id)
);
Layer 5 — Admin & Analytics
sql
-- ENQUIRIES: Contact/support requests from landing page
CREATE TABLE enquiries (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT,
    phone       TEXT,
    school_name TEXT,
    std_class   SMALLINT,
    message     TEXT,
    status      VARCHAR(20) DEFAULT 'new',   -- new, contacted, resolved
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- QUESTION_STATS: Rolling statistics per question (for admin insights)
-- Updated via DB trigger after each attempt submission
CREATE TABLE question_stats (
    question_id         INT PRIMARY KEY REFERENCES questions(id),
    total_attempts      INT DEFAULT 0,
    correct_count       INT DEFAULT 0,
    wrong_count         INT DEFAULT 0,
    skip_count          INT DEFAULT 0,
    avg_time_seconds    NUMERIC(6,2) DEFAULT 0,
    difficulty_actual   NUMERIC(4,3),           -- computed: wrong/total
    -- e.g. 0.85 means 85% students got it wrong → actually hard
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 📐 Complete ERD Relationships
```
exam_events ──< exams ──< sections ──< topics
                  │              │
                  ├──< question_contexts
                  │
                  └──< questions >──── sections
                            │    └──── topics
                            │    └──── question_contexts
                            └──< options

user_profiles >──< parent_student_links

user_profiles ──< exam_assignments >── exams
user_profiles ──< attempts >────────── exams
                     └──────< responses >── questions
```

---

## 🎯 Key Design Decisions Explained

**1. `question_contexts` is separate from `questions`**
Because Q1 and Q2 both reference the SAME Bal Gandharva passage — you store the passage once, not twice. Same for Intelligence Test instructions that cover Q27+Q28.

**2. `section_scores` and `topic_scores` stored as JSONB in `attempts`**
Computing these live on every API call is expensive. They get computed once on submit, stored as JSON. Fast reads forever.

**3. `question_type` enum drives frontend rendering**
The React component reads this field and decides whether to render a text question, show a context panel, render an image option grid, etc. DB tells the UI what to do.

**4. `responses.visit_count` and `is_marked_review`**
These power the question palette (gray/white/green/orange colors). Stored per-response so exam state can be fully restored on page refresh.

**5. `question_stats` as a separate table updated by trigger**
Admin can see " Q47 has 78 % wrong rate " without running expensive aggregations. DB trigger keeps it fresh automatically.

---

## 📋 Supabase Table Creation Order
```
1. exam_events
2. exams
3. sections
4. topics
5. question_contexts
6. questions
7. options
8. user_profiles         ← after Supabase Auth setup
9. parent_student_links
10. exam_assignments
11. attempts
12. responses
13. enquiries
14. question_stats       ← + trigger setup
```

---

## 🔑 Supabase-Specific Notes
```
ROW LEVEL SECURITY (RLS) policies needed:
- questions:      read if exam is_active=true
- attempts:       student can only read/write their own
- responses:      student can only read/write their own attempt's responses  
- user_profiles:  student reads own + parent reads linked children
- exam_assignments: student reads own assignments only
- enquiries:      insert only (no auth needed for contact form)

INDEXES to create:
- questions(exam_id, question_no)
- responses(attempt_id)          ← heavy read during exam
- attempts(student_id, status)   ← dashboard queries
- attempts(exam_id)              ← admin reports
This gives you a solid foundation. Want me to generate the actual Supabase SQL migration file you can paste and run directly in the Supabase SQL editor to create all these tables at once?

ok but this should be multilingual so i think the question table should handle multingwal. just keep it open we will start english and marathi first. 
also we need to insert Answer's ans explanations in it also so that we can explain what went wrong. once the exam is finish. 
authontication and authorization should handle parent and student sessions. 
also it should support google facebook type of authontication as well as it shoudl also support the custom login also. 
we are starting very with one exam but we want to grow with diffrent exams also. so keep the option for scale. once done create a one sql query which i can provide the claude code.

2:27 PM

Architected scalable multilingual exam platform with integrated authentication
Architected scalable multilingual exam platform with integrated authentication
The user wants:

Multilingual support (start with English + Marathi, scalable)
Answers and explanations in the question table
Auth supporting parent + student sessions, Google/Facebook + custom login
Scalable for multiple exam types
One complete SQL query for Claude Code
Let me design the final schema and write the complete SQL.


Check if there's a relevant skill
The user wants a complete SQL file for Supabase. Let me create this properly with:

Multilingual support (EN + MR, extensible)
Answers and explanations in questions
Auth supporting parent + student + Google/Facebook + custom login
Scalable for multiple exam types
Let me write the complete SQL migration file.


Complete Supabase SQL migration for ScholarPath exam portal
scholarpath_migration.sql

Copy to outputs and count lines

Script

Presented file
The SQL file is created and ready. Let me provide a clear summary of what was built.

Done
Here's the complete 1,124-line SQL migration file ready to paste into Supabase SQL Editor. Here's what it solves for each of your requirements:

Multilingual — every user-facing text column follows the _en / _mr pattern throughout questions, options, topics, sections, and notifications. To add Hindi later it's just ALTER TABLE questions ADD COLUMN text_hi TEXT — nothing else breaks.

Answers + Explanations — correct_option, explanation_en, explanation_mr, hint_en, hint_mr are all in the questions table. The v_exam_questions view deliberately excludes correct answers (safe for exam delivery), while v_exam_answers exposes them only for post-exam review.

Auth — Google, Facebook, and Custom login — Supabase Auth handles all three out of the box. The handle_new_auth_user trigger auto-creates a user_profiles row the moment any user signs up, regardless of provider. Parent and student sessions are differentiated by the role enum and the parent_student_links table enforces who can see whose data via RLS policies.

Scalable for multiple exams — the exam_boards → exam_categories → exam_events → exams hierarchy means you can add CBSE, SSC, or 8th std exams without touching existing data.

To run it: paste the entire file into Supabase → SQL Editor → Run. Then enable Google and Facebook in your Supabase Auth dashboard under Authentication → Providers.

Scholarpath migration
Code · SQL 
what are the recommended claude skills for this application.

9:09 PM

Evaluated skill relevance for exam portal application
Evaluated skill relevance for exam portal application





Great question — based on everything we've designed for ScholarPath, here's my honest assessment of which skills are worth using and when:

frontend-design — Use this every time you build a UI component. The exam interface, question palette, result page, and parent dashboard all need to look polished and professional, not generic. This skill specifically prevents the " AI - made " look and pushes toward production-grade quality. This is your most important skill for this project.

pdf — Directly relevant in two places. First, generating the post-exam PDF report card that students and parents can download and share with schools. Second, if you want to let admins upload existing MSCE question paper PDFs and extract content for bulk import. Both are real features in your roadmap.

xlsx — You'll need this for the admin side. Bulk importing questions via Excel spreadsheet (much easier for content teams than JSON), exporting student performance reports for schools, and generating district-level analytics. Your admin dashboard will almost certainly need Excel export at some point.

docx — Useful but lower priority. If you want to generate formatted question papers or detailed student progress reports as Word documents that teachers can print or edit, this comes in handy. Not day-one critical but useful once the core is working.

pptx — Probably not needed for the application itself, but could be useful if you're ever presenting ScholarPath to schools or investors and want to auto-generate a performance summary deck. Low priority.

skill-creator — Worth knowing about. Once your workflow stabilizes, you could create a custom " scholarpath " skill that captures your specific DB schema, module contracts, and coding conventions — so every future Claude Code session starts with full context without you re-explaining the architecture.

The practical order for your build would be: frontend-design first (exam interface is your hardest UI challenge), then pdf (report cards), then xlsx (question bulk import for admin). The rest as needed.

ok what about the pdp skills for my project every time i create new context how should i know that i should have correct ADRs

9:22 PM

Deciphered project documentation needs and ADR maintenance strategy
Deciphered project documentation needs and ADR maintenance strategy




Good question — you're really asking two things: how to create a project knowledge file so every new Claude Code session starts with full context, and how to know when to write a new ADR.

The Project Knowledge File (CLAUDE.md)
Claude Code automatically reads a CLAUDE.md file from your project root. This is your most powerful tool. Every new session, every new context window — Claude reads this first.

Here's what your ScholarPath CLAUDE.md should contain:

markdown
# ScholarPath — Project Knowledge File

## What This Is
Maharashtra MSCE scholarship exam portal for 5th and 8th std students.
Multilingual: English + Marathi first, Hindi-ready architecture.

## Tech Stack
Backend:  Python FastAPI + SQLAlchemy 2.0 + Supabase (PostgreSQL)
Frontend: React 18 + Vite + Tailwind + Zustand + react-i18next
Auth:     Supabase Auth (Google + Facebook + Email, handled by trigger)
Deploy:   Vercel (FE) + Render (BE) + Supabase (DB)

## Module Boundaries (NEVER cross these)
auth     → owns: users table auth columns. Exposes: verify_token()
user     → owns: user_profiles. Consumes: auth only
catalog  → owns: exam_boards, exam_events, exams, sections, topics
question → owns: questions, options, question_contexts
attempt  → owns: attempts, responses. Does NOT calculate scores
analysis → owns: nothing. Read-only. Pure computation only
media    → owns: file storage. Provider pattern (local dev / cloudinary prod)
admin    → orchestrator only. Zero business logic lives here

## DB Rules
- Multilingual columns: always _en + _mr pairs (add _hi later via ALTER TABLE)
- correct_option: NEVER sent to frontend during active exam
- Scores computed ONCE on submit, stored as JSONB in attempts table
- question_stats updated by DB trigger — never in application code

## Exam Structure
Paper 0501: Section I Q1-25 English | Section II Q26-75 Mathematics
Paper 0502: Section I Q1-25 Marathi | Section II Q26-75 Intelligence Test
75 questions × 2 marks = 150 marks | 90 minutes

## Question Types
text, text_image, image_only, context_text, 
context_image, marathi_only, bilingual

## RLS Pattern
Students see own data only.
Parents see linked children's data via parent_student_links.
Admins bypass via is_admin() helper function.

## ADR Location
All architecture decisions: /docs/adr/
Current ADRs: ADR-001 through ADR-008 (see /docs/adr/)

## What AI Should NOT Do
- Never add business logic to admin module
- Never query correct_option in exam delivery endpoints
- Never compute scores in attempt module
- Never import module internals across module boundaries
```

---

## How to Know When You Need a New ADR

The trigger is simple: **any time you or Claude are about to make a decision that will be hard to reverse or that affects multiple modules**, write an ADR first. Here are the specific signals to watch for:

**Write an ADR when someone asks " should we..."**
```
" Should we cache questions in Redis ? "          → ADR-009: Caching Strategy
" Should we use WebSockets for auto - save ? "      → ADR-010: Real-time Communication  
" Should we store images in Supabase Storage ? "  → ADR-011: Media Storage
" Should we
add Hindi now
    or later ? "            → ADR-012: Language Expansion
" Should analysis be async
    or sync ? "            → ADR-013: Analysis Processing
```

**Write an ADR when a module boundary is unclear**
```
Claude suggests: " Let me
add scoring logic to the attempt module..."
Stop. That violates ADR-005. If you're unsure, that uncertainty IS the ADR.
```

**Write an ADR when you're choosing between two real options**
```
Not needed: " Should we use a for loop
    or map ? " → trivial, no ADR
Needed:     " Should we use JWT
    or Supabase sessions ? " → ADR affects auth module forever
ADR Template (keep it short — one page max)
Create /docs/adr/ADR-009-caching-strategy.md:

markdown
# ADR-009: Caching Strategy for Exam Questions

**Date:** 2025-02-21  
**Status:** Accepted  
**Decider:** Preetam

## Context
Catalog module (exam list, questions) is read-heavy. 
Same 75 questions served to potentially hundreds of students simultaneously.

## Decision
Add in-memory cache using fastapi-cache2 on CatalogService.get_exam() 
and QuestionService.get_questions_for_exam(). 
Cache key: exam_id + language. TTL: 1 hour.
Redis when traffic grows (swap via env var CACHE_BACKEND).

## Alternatives Considered
1. No cache (simple, but will struggle under load)
2. Redis from day one (over-engineering for current scale)
3. CDN cache on API responses (good later, not now)

## Consequences
+ Fast question delivery under load
+ Easy to swap to Redis later (interface already abstracted)
- Cache invalidation needed when admin edits questions
- Add cache.clear(exam_id) to admin question update endpoint

## Module Impact
catalog/service.py — add @cache decorator
question/service.py — add @cache decorator  
admin/router.py    — add cache clear on question update
```

---

## Practical Workflow for Your Project

Every time you open a new Claude Code session, do this:
```
1. Claude reads CLAUDE.md automatically → full context restored
2. You describe what you're building today
3. If the task crosses a module boundary → check ADR first
4. If no ADR exists for this decision → write one before coding
5. After coding → update CLAUDE.md if anything structural changed
The key insight from your article: AI fills the context window, you protect the boundaries. CLAUDE.md is what makes that repeatable across sessions without you re-explaining everything every single time.

Want me to generate your complete CLAUDE.md + all 8 ADR files as a ready-to-use /docs folder structure you can drop straight into your project?

Yes genrate complete ADR for this.

9:24 PM

Assembled comprehensive ADR documentation from all files
Assembled comprehensive ADR documentation from all files









All 14 files are ready — here's what's in the package:

CLAUDE.md (275 lines) — Drop this in your project root. Claude Code reads it automatically on every session. It covers tech stack, all 8 module boundaries, DB rules, exam structure, question types, frontend patterns, env variables, and the " what AI should NOT do " guardrails.

ADR-TEMPLATE.md — Your blank template for every future decision.

12 ADRs covering every major decision:

ADR	Covers
001	Supabase Auth — Google, Facebook, Email, trigger auto-creates profile
002	Vertical slice architecture — why, how, module boundaries
003	Multilingual _en / _mr column pattern — how to add Hindi later
004	Question content model — 7 types, context table, options table
005	Attempt state machine — per-answer autosave, resume on refresh, timer
006	Score computation — pure functions, stored as JSONB on submit
007	Media storage — LocalProvider dev / Cloudinary prod via env var
008	Supabase as DB platform — free tier, RLS, UptimeRobot ping trick
009	Parent-student auth — join table, RLS helper, read-only parent access
010	Frontend Zustand stores — one per module, optimistic autosave pattern
011	Exam scalability — 4-level hierarchy, new exams = data only, no code
012	Answer security — two DB views, correct_option never in exam delivery
How to use in your project:

scholarpath/
├── CLAUDE.md          ← project root
├── docs/
│   └── adr/
│       ├── ADR-TEMPLATE.md
│       ├── ADR-001-...md
│       └── ...
When starting a new Claude Code session, just say " read CLAUDE.md first " and every decision, boundary, and rule is instantly restored.

Claude
Document · MD 
Adr 001 authentication strategy
Document · MD 
Adr 002 vertical slice architecture
Document · MD 
Adr 003 multilingual data design
Document · MD 
Adr 004 question content model
Document · MD 
Adr 005 exam attempt state machine
Document · MD 
Adr 006 score computation strategy
Document · MD 
Adr 007 media storage provider pattern
Document · MD 
Adr 008 database platform selection
Document · MD 
Adr 009 parent student authorization model
Document · MD 
Adr 010 frontend module communication
Document · MD 
Adr 011 exam scalability model
Document · MD 
Adr 012 question answer security
Document · MD 
Adr template
Document · MD 
give me short answer what is adr template

9:40 PM
An ADR (Architecture Decision Record) is a short document that captures why you made a technical decision, not just what you decided.

Think of it as a diary entry for your codebase. When you or Claude Code asks 6 months later " why did we build it this way ? " — the ADR has the answer.

One ADR = one decision. It answers 4 questions:

What's the situation? (Context)
What did we decide? (Decision)
What else did we consider? (Alternatives)
What did we gain/lose? (Consequences)
Real example from your project:

" Why do we use Supabase Auth instead of building our own login ? " → ADR-001 answers this: we considered custom JWT, Auth0, and Supabase — chose Supabase because Google/Facebook login works with zero backend code, and auth.uid() integrates directly with our RLS policies.

Without the ADR, you or Claude Code would guess the reason, potentially undo the decision, and create bugs.

The template is just the blank form with those 4 sections pre-filled — so every ADR in your project has the same structure and you never forget what to write.

ok as you know the proejct and the DB create a modular approch coding prompt. i have one article understand that article and create comprehinsive prompt. for the project. 
the article i am giving is for the guidance . We might not need to use all but most of them are very helpfull. 
L;DR I use AI coding tools for scaffolding, tests, docs, and boring boilerplate. Architecture and module boundaries stay human‑led. We broke the app into small vertical slices, added guardrails, and shipped faster.
The Real Problem

Large applications slow down as complexity grows.
Code reviews take longer as dependencies multiply.
Once the codebase exceeds the model’s context window, AI becomes unreliable.
I worked on a similar application and learned how to keep a mid‑to‑large system clean as it scales.
The Core Approach
Break the application into small, focused modules (Auth, Payments, Notifications, Search, etc.).
Give each module a clear contract (OpenAPI, AsyncAPI, typed interfaces).

Boundaries — What belongs inside each module
Communication patterns — REST, events, or shared types
Data ownership & consistency — including CDC when needed
Cross‑cutting guardrails — auth, security, rate limits, uptime
Testing strategy
Security testing
Repo + delivery strategy
Where to avoid using AI
Where AI Helps (and Where It Doesn’t)
Where AI Helps

Scaffolding: controllers, services, repositories, DTOs, validation pipelines
Boilerplate: logging, error handling, config, DI, authorization setup
Tests: unit tests, contract tests, test data, basic security tests
Documentation: READMEs, API examples, module guides
Refactoring: renaming, restructuring, cleanup
Where AI Hurts

Architecture decisions
Complex business logic (edge cases, conditions, failure modes)
Security‑critical components
Anything involving sensitive code
AI is an assistant — not the architect.
Pros

Speed: huge boost for repetitive work
Consistency: cleaner naming and patterns
Source control: easier merges and commit hygiene with structured prompts
Better documentation: faster to create and update
Less time wasted on syntax issues
Cons

Quality drift: code looks right but isn’t safe
Contract drift: modules misalign if not enforced
Shallow tests: AI defaults to happy paths
Privacy & licensing concerns
Architecture erosion: quick fixes break long‑term integrity
Without reviews, expertise, contract tests, and security checks, you’ll hit a wall.
My Workflow

Strong context + knowledge files (clean system prompt, templates, cleanup routines)
One‑page module ADRs for Users, Auth, Payments, Notifications, Search
Contracts‑first approach using OpenAPI + AsyncAPI
Scaffold with AI — one module at a time
Add guardrails (coding standards, formatting, security scans, contract tests)
Ship vertical slices — API + UI + tests per module
Document continuously — READMEs, API examples, ADRs
Final Thought
AI accelerates the productivity. Architecture protects
Use both intentionally to build fast and build clean.
understanding this create a development prompt.

Show more
9:42 PM

Synthesized article workflow to enhance modular coding prompt comprehensively
Synthesized article workflow to enhance modular coding prompt comprehensively






The file I generated earlier is already done — let me enhance it with the article's specific workflow steps more explicitly mapped, then present it.


Created a file, ran a command, read a file
Created a file, ran a command, read a file
682-line prompt built directly from the article's methodology applied to your project. Here's how it maps:

Article → Prompt

The article's 7 workflow steps became Section 1 — load context → ADR check → contract first → scaffold → guardrails → ship vertical slice → document. Every session follows this order.

" Give each module a clear contract " became Section 3 — schemas written and reviewed before any implementation. This is what prevents contract drift between modules.

" AI defaults to happy paths " became Section 6 — explicit test templates for unit tests, integration tests, and security tests (the ones AI always skips). Things like " student cannot see another student 's attempt" and "correct_option not in exam delivery" are written out as test stubs you paste in.

"Where AI hurts" became Section 7 — a hard list of what AI must never generate (auth logic, migrations, RLS policies, scoring rules).

How to use it in Claude Code:

Paste the entire file at the start of every new session
Use the task format in Section 10 — it forces you to name the module, the ADR, and the acceptance criteria before any code is written
Run the checklist in Section 9 before closing the session
Development prompt
Document · MD 
do we need to create data base strcutre first before we start the website ?

9:50 PM

Deciphered question about database-first development sequencing
Deciphered question about database-first development sequencing

Yes — database first. Always.

Here' s the simple reason: every module in your project depends on the DB schema.If you start building the attempt module before the questions table exists,
    you 'll scaffold against assumptions that turn out to be wrong — then rewrite everything.

The practical order for ScholarPath:

1. DB Schema (already done ✅)
   Run scholarpath_migration.sql in Supabase SQL Editor.
   All 18 tables, triggers, RLS policies, seed data — one shot.

2. Backend foundation
   FastAPI setup → auth module → user module
   These need user_profiles table to exist first.

3. Seed real data
   Insert actual MSCE 2025 questions via bulk importer.
   You need real data to test exam flow — not just empty tables.

4. Backend modules
   catalog → question → attempt → analysis
   Each one builds on the tables below it.

5. Frontend
   Now you build UI against real working APIs.
   No guessing — every component has a real endpoint to call.
What goes wrong if you skip DB first:

The frontend team builds a result page expecting section_scores as an array — but the backend stored it differently. Now you' re changing both the DB
    and the API contract mid - build.That 's the "contract drift" the article warns about.

Good news — you' re already ahead.Your DB migration is complete
    and your ADRs document every decision.The schema won 't surprise you mid-build.

So the answer is: run the migration SQL in Supabase today, then start Phase 1 of the development prompt tomorrow. That' s the right starting point.ok DB is created will the prompt work
    and understand the data base ? 10 :06 PM Evaluated prompt sufficiency for database context comprehension Evaluated prompt sufficiency for database context comprehension Short answer: Not automatically.The prompt alone is not enough.Claude Code reads files
from your project — it doesn 't magically know your Supabase schema. Here' s what actually happens
    and what you need to do: What Claude Code reads automatically: ✅ CLAUDE.md (
        if it 's in project root)
✅ Any file you paste or reference in the session
✅ Files you tell it to read
❌ Your live Supabase database  (it cannot connect to it)
❌ The migration SQL unless you tell it where it is
The fix — 3 things to add to your project:

1. Put the migration SQL in your repo

scholarpath/
├── CLAUDE.md
├── database/
│   └── scholarpath_migration.sql   ← already generated ✅
Then add one line to CLAUDE.md:

## Database Schema
Full schema: /database/scholarpath_migration.sql
Run this file in Supabase SQL Editor to recreate the DB.
2. Add a schema summary directly inside CLAUDE.md

Claude Code reads CLAUDE.md on every session. Put the key tables there so it doesn' t need to read the whole SQL file every time: markdown ## Key Tables (quick reference)
        exam_boards → exam_categories → exam_events → exams → sections → topics question_contexts → questions → options user_profiles → parent_student_links exam_assignments → attempts → responses question_stats | exam_stats | enquiries | notifications ## Views (use these, not raw tables)
        v_exam_questions → exam delivery (correct_option EXCLUDED) v_exam_answers → post - exam review only v_student_attempts → dashboard queries ```

**3. In each Claude Code session, explicitly say:**
``` Read CLAUDE.md
        and / database / scholarpath_migration.sql before writing any models
        or queries.Why this matters practically:
        When Claude Code writes question / models.py,
        it needs to know the exact column names — text_en,
        text_mr,
        question_type,
        correct_option —
        or it will invent column names that don 't match your real DB. One wrong column name = runtime error.

With the SQL file in the repo and referenced in CLAUDE.md, Claude Code reads the exact schema you already built and generates models that match it perfectly.

Want me to update your CLAUDE.md now to include the schema summary section? That way the whole context package — CLAUDE.md + ADRs + migration SQL — works together as one complete knowledge base for every session.

yes do it

10:07 PM

Architected comprehensive database schema documentation
Architected comprehensive database schema documentation


Good — now I' ll inject the full schema section right
        after the existing "Database — Key Rules" block.Edited a file,
            ran a command,
            read a file Edited a file,
            ran a command,
            read a file
        Add complete database schema section
        after the key rules block CLAUDE.md + 387 -3 Check final line count bash wc - l / mnt / user - data / outputs / CLAUDE.md Output 659 / mnt / user - data / outputs / CLAUDE.md Presented file Done Done.CLAUDE.md is now 659 lines
            and contains the complete database schema built into it.What was added — every table with exact column names: Every single column in all 18 tables is now documented with its exact name,
            data type,
            FK relationships,
            constraints,
            and defaults.So
            when Claude Code writes question / models.py,
            it reads: text_en TEXT -- NULL for image_only or marathi_only
            text_mr TEXT -- NULL for english-only questions
            correct_option SMALLINT NOT NULL CHECK (1 -4)...and generates the SQLAlchemy model with those exact column names — no guessing,
            no mismatches.Also included: All 8 ENUMs with every valid value All 3 views (
                v_exam_questions,
                v_exam_answers,
                v_student_attempts
            )
            and
            when to use each All 6 triggers with a note saying "never replicate in app code" The 3 RLS helper functions (is_admin(), parent_can_see_student()) All indexes so Claude Code knows which columns to use in
        WHERE clauses Seeded data so it knows what 's already in the DB
How to use now:

scholarpath/
├── CLAUDE.md                    ← paste this in every session
├── database/
│   └── scholarpath_migration.sql ← reference if Claude needs the full SQL
├── docs/adr/                    ← read before touching any module
Every Claude Code session starts with one instruction: "Read CLAUDE.md first." Everything it needs to write correct, schema-matching code is in that one file.

Claude
Document · MD 




Claude is AI and can make mistakes. Please double-check responses.
Scholarpath migration · SQL
Copy

-- ============================================================
-- SCHOLARPATH — Complete Supabase Database Migration
-- Version: 1.0.0
-- Languages: English + Marathi (extensible pattern)
-- Auth: Supabase Auth (supports Google, Facebook, Email/Password)
-- ============================================================
-- 
-- EXECUTION ORDER:
-- 1. Run this entire file in Supabase SQL Editor
-- 2. Enable Google + Facebook OAuth in Supabase Auth dashboard
-- 3. Enable RLS in Supabase dashboard for all tables
--
-- MULTILINGUAL DESIGN PATTERN:
-- All user-facing text columns follow: column_en, column_mr
-- To add Hindi later: ALTER TABLE ... ADD COLUMN column_hi TEXT;
-- ============================================================


-- ============================================================
-- EXTENSIONS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- for future full-text search on questions


-- ============================================================
-- ENUMS — Central type definitions (easy to extend)
-- ============================================================

CREATE TYPE user_role AS ENUM (' student ', ' parent ', ' teacher ', ' exam_admin ', ' super_admin ');

CREATE TYPE medium_type AS ENUM (' english ', ' marathi ', ' hindi ', ' semi_english ');

CREATE TYPE question_type AS ENUM (
    ' text ',            -- Pure text question + text options (most common)
    ' text_image ',      -- Text question + image embedded in question
    ' image_only ',      -- Image IS the question (Intelligence Test figures)
    ' context_text ',    -- Belongs to a passage/poem context
    ' context_image ',   -- Belongs to a pictograph/figure context
    ' marathi_only ',    -- No English version (Marathi section in Paper II)
    ' bilingual '        -- Shown simultaneously in EN + MR
);

CREATE TYPE attempt_status AS ENUM (' ongoing ', ' submitted ', ' expired ', ' abandoned ');

CREATE TYPE assignment_type AS ENUM (' practice ', ' assigned ', ' mock_test ');

CREATE TYPE context_type AS ENUM (
    ' paragraph ',
    ' poem ',
    ' advertisement ',
    ' image ',
    ' pictograph ',
    ' instruction ',
    ' venn_diagram ',
    ' figure_series ',
    ' table ',
    ' data_chart '
);

CREATE TYPE difficulty_level AS ENUM (' easy ', ' medium ', ' hard ');

CREATE TYPE enquiry_status AS ENUM (' new ', ' contacted ', ' resolved ', ' spam ');


-- ============================================================
-- LAYER 1: EXAM CATALOG
-- ============================================================

-- Exam board / organization that conducts exams
-- e.g. MSCE, CBSE, SSC — designed for scale from day one
CREATE TABLE exam_boards (
    id          SERIAL PRIMARY KEY,
    name_en     TEXT NOT NULL,
    name_mr     TEXT,
    short_code  VARCHAR(20) UNIQUE NOT NULL,    -- ' MSCE ', ' CBSE ', ' SSC '
    state       TEXT,                           -- ' Maharashtra ', ' National '
    website_url TEXT,
    logo_url    TEXT,
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Exam categories / types
-- e.g. ' Scholarship ', ' Competitive ', ' Board Exam ', ' Entrance Test '
CREATE TABLE exam_categories (
    id          SERIAL PRIMARY KEY,
    board_id    INT REFERENCES exam_boards(id) ON DELETE CASCADE,
    name_en     TEXT NOT NULL,
    name_mr     TEXT,
    description_en  TEXT,
    description_mr  TEXT,
    icon_url    TEXT,
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Exam events: one annual event (e.g. "MSCE Scholarship 2025")
-- Groups all papers of that event together
CREATE TABLE exam_events (
    id              SERIAL PRIMARY KEY,
    board_id        INT REFERENCES exam_boards(id),
    category_id     INT REFERENCES exam_categories(id),
    
    title_en        TEXT NOT NULL,
    title_mr        TEXT,
    
    std_class       SMALLINT NOT NULL,          -- 5 or 8 (or NULL for open exams)
    year            SMALLINT NOT NULL,          -- 2025
    
    exam_date       DATE,
    registration_deadline DATE,
    
    description_en  TEXT,
    description_mr  TEXT,
    
    is_active       BOOLEAN DEFAULT false,      -- Admin publishes manually
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Individual exam papers (Paper I = 501, Paper II = 502)
CREATE TABLE exams (
    id              SERIAL PRIMARY KEY,
    event_id        INT REFERENCES exam_events(id) ON DELETE CASCADE,
    
    paper_code      VARCHAR(10) NOT NULL,       -- ' 501 ', ' 502 ', ' 801 ', ' 802 '
    set_code        VARCHAR(5) DEFAULT ' A ',     -- A, B, C, D (different sets)
    paper_number    SMALLINT,                   -- 1, 2
    
    title_en        TEXT NOT NULL,
    title_mr        TEXT,
    
    -- What medium this paper is for
    medium          medium_type DEFAULT ' english ',
    
    total_questions SMALLINT DEFAULT 75,
    total_marks     SMALLINT DEFAULT 150,
    marks_per_question SMALLINT DEFAULT 2,
    duration_minutes SMALLINT DEFAULT 90,
    
    -- Instruction text shown before exam starts
    instructions_en TEXT,
    instructions_mr TEXT,
    
    is_active       BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(paper_code, set_code)
);

-- Sections within a paper (Section I = Language, Section II = Math/Intelligence)
CREATE TABLE sections (
    id              SERIAL PRIMARY KEY,
    exam_id         INT REFERENCES exams(id) ON DELETE CASCADE,
    
    section_label   VARCHAR(5) NOT NULL,        -- ' I ', ' II '
    subject_en      TEXT NOT NULL,              -- ' English ', ' Mathematics ', ' Intelligence Test '
    subject_mr      TEXT,                       -- ' गणित ', ' बुद्धिमत्ता चाचणी '
    
    question_from   SMALLINT NOT NULL,          -- 1
    question_to     SMALLINT NOT NULL,          -- 25
    order_index     SMALLINT DEFAULT 1,
    
    -- For analysis color coding in result page
    color_hex       VARCHAR(7) DEFAULT ' #3B82F6'
    );
-- Topics / sub-topics for analysis (e.g. Grammar, Fractions, Mirror Images)
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    section_id INT REFERENCES sections(id) ON DELETE CASCADE,
    name_en TEXT NOT NULL,
    name_mr TEXT,
    description_en TEXT,
    description_mr TEXT,
    order_index SMALLINT DEFAULT 1
);
-- ============================================================
-- LAYER 2: QUESTION BANK
-- ============================================================
-- Question contexts: passages, poems, instructions that multiple questions share
-- Q1-2 share one passage → stored once here, referenced by both questions
CREATE TABLE question_contexts (
    id SERIAL PRIMARY KEY,
    exam_id INT REFERENCES exams(id) ON DELETE CASCADE,
    context_type context_type NOT NULL,
    -- Title (e.g. "The House Next Door", "Bal Gandharva")
    title_en TEXT,
    title_mr TEXT,
    -- Main text content (passage / poem / instructions)
    content_en TEXT,
    content_mr TEXT,
    -- For image-based contexts (pictograph, figure, advertisement image)
    image_url TEXT,
    image_alt_en TEXT,
    -- accessibility description
    image_alt_mr TEXT,
    -- For Intelligence Test directions like "Q27-28: Select the mirror image..."
    instruction_en TEXT,
    instruction_mr TEXT,
    -- Which questions use this context
    applies_from SMALLINT,
    -- Q no. from
    applies_to SMALLINT,
    -- Q no. to
    order_index SMALLINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- QUESTIONS: Core content table with full multilingual support
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    exam_id INT REFERENCES exams(id) ON DELETE CASCADE,
    section_id INT REFERENCES sections(id),
    topic_id INT REFERENCES topics(id),
    context_id INT REFERENCES question_contexts(id),
    -- NULL if standalone
    question_no SMALLINT NOT NULL,
    question_type question_type NOT NULL DEFAULT 'text',
    -- Question text — add more languages as: text_hi TEXT, text_gu TEXT, etc.
    text_en TEXT,
    -- NULL if image_only type
    text_mr TEXT,
    -- NULL if english-only question
    -- For questions where image IS part of the question (not context)
    -- e.g. "How many triangles in this figure?" [figure embedded in question]
    question_image_url TEXT,
    question_image_alt_en TEXT,
    question_image_alt_mr TEXT,
    -- THE ANSWER
    correct_option SMALLINT NOT NULL CHECK (
        correct_option BETWEEN 1 AND 4
    ),
    -- EXPLANATION — shown after exam to explain why the answer is correct
    explanation_en TEXT,
    explanation_mr TEXT,
    -- Optional: extra hint shown during practice mode (not during test)
    hint_en TEXT,
    hint_mr TEXT,
    marks SMALLINT DEFAULT 2,
    difficulty difficulty_level DEFAULT 'medium',
    -- Admin tags for filtering and future AI features
    -- e.g. ['ordinal_numbers', 'grammar', 'fill_in_blank']
    tags TEXT [] DEFAULT '{}',
    -- Rolling statistics (updated by trigger after each attempt submission)
    attempt_count INT DEFAULT 0,
    correct_count INT DEFAULT 0,
    -- Computed: correct_count / attempt_count — actual difficulty from real data
    -- NULL until at least 10 attempts
    actual_difficulty_ratio NUMERIC(4, 3),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(exam_id, question_no)
);
-- OPTIONS: 4 options per question
-- Handles: text-only, image-only, or both (bilingual Intelligence Test options)
CREATE TABLE options (
    id SERIAL PRIMARY KEY,
    question_id INT REFERENCES questions(id) ON DELETE CASCADE,
    option_no SMALLINT NOT NULL CHECK (
        option_no BETWEEN 1 AND 4
    ),
    -- Text options — add text_hi for Hindi support later
    text_en TEXT,
    -- NULL for image-only options
    text_mr TEXT,
    -- Image options (Intelligence Test: all 4 options are figures)
    image_url TEXT,
    -- NULL for text-only options
    image_alt_en TEXT,
    image_alt_mr TEXT,
    -- is_correct is REDUNDANT (use questions.correct_option) but
    -- kept here for query convenience — always in sync via trigger
    is_correct BOOLEAN DEFAULT false,
    UNIQUE(question_id, option_no)
);
-- ============================================================
-- LAYER 3: USERS & AUTH
-- ============================================================
-- Supabase Auth handles auth.users automatically for:
--   Email/Password login  → works out of the box
--   Google OAuth         → enable in Supabase Auth dashboard
--   Facebook OAuth       → enable in Supabase Auth dashboard
-- 
-- auth.users stores: id (UUID), email, created_at, last_sign_in_at
-- We extend it with our business data in user_profiles
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    -- Core info
    full_name TEXT NOT NULL,
    role user_role NOT NULL DEFAULT 'student',
    avatar_url TEXT,
    phone TEXT,
    -- Preferred language for UI (drives default question language)
    preferred_language VARCHAR(5) DEFAULT 'en',
    -- 'en', 'mr', 'hi'
    -- Student-specific fields (NULL for parents/admins)
    std_class SMALLINT,
    -- 5 or 8
    medium medium_type,
    school_name TEXT,
    district TEXT,
    state TEXT DEFAULT 'Maharashtra',
    date_of_birth DATE,
    -- Auth provider tracking (for analytics — actual OAuth in Supabase)
    -- Values: 'email', 'google', 'facebook'
    auth_provider TEXT DEFAULT 'email',
    -- Account status
    is_active BOOLEAN DEFAULT true,
    is_onboarded BOOLEAN DEFAULT false,
    -- has completed profile setup
    -- For future premium features
    subscription_tier VARCHAR(20) DEFAULT 'free',
    -- 'free', 'basic', 'premium'
    subscription_expiry TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Parent → Student relationships
-- One parent can monitor multiple children
-- One student can have multiple parents monitoring them
CREATE TABLE parent_student_links (
    id SERIAL PRIMARY KEY,
    parent_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    -- Parent gives a nickname for the child in their dashboard
    child_nickname TEXT,
    -- Who created this link (parent self-linked or admin added)
    linked_by UUID REFERENCES user_profiles(id),
    linked_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(parent_id, student_id),
    -- A parent cannot link to themselves
    CHECK(parent_id != student_id)
);
-- ============================================================
-- LAYER 4: EXAM ASSIGNMENT & ATTEMPTS
-- ============================================================
-- Exam assignments: which exams are available to which students
-- Types:
--   'practice'   → student self-starts any time (open access)
--   'assigned'   → exam_admin assigned to specific student(s)
--   'mock_test'  → timed, simulated real exam conditions
CREATE TABLE exam_assignments (
    id SERIAL PRIMARY KEY,
    exam_id INT REFERENCES exams(id) ON DELETE CASCADE,
    student_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES user_profiles(id),
    -- NULL for self-practice
    assignment_type assignment_type DEFAULT 'practice',
    max_attempts SMALLINT DEFAULT 10,
    -- how many times allowed to retake
    attempts_used SMALLINT DEFAULT 0,
    -- cache counter
    -- Time window when exam can be taken (NULL = no restriction)
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(exam_id, student_id)
);
-- Attempts: one row = one complete exam session
CREATE TABLE attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES user_profiles(id),
    exam_id INT NOT NULL REFERENCES exams(id),
    assignment_id INT REFERENCES exam_assignments(id),
    attempt_number SMALLINT DEFAULT 1,
    -- 1st, 2nd, 3rd attempt at same exam
    status attempt_status DEFAULT 'ongoing',
    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    last_saved_at TIMESTAMPTZ DEFAULT NOW(),
    duration_seconds INT,
    -- actual time taken (computed on submit)
    -- Final scores (NULL until submitted)
    total_score SMALLINT,
    total_correct SMALLINT,
    total_wrong SMALLINT,
    total_skipped SMALLINT,
    percentage NUMERIC(5, 2),
    grade VARCHAR(20),
    -- 'Excellent', 'Good', 'Average', 'Below Average'
    -- Section-wise breakdown stored as JSON (computed once on submit, fast to read)
    -- Example: [{"section_id": 1, "label": "I", "subject": "English",
    --            "score": 38, "total": 50, "percentage": 76.0}]
    section_scores JSONB DEFAULT '[]',
    -- Topic-wise breakdown stored as JSON (computed once on submit)
    -- Example: [{"topic_id": 3, "name": "Grammar", "correct": 4,
    --            "total": 5, "percentage": 80, "status": "strong"}]
    topic_scores JSONB DEFAULT '[]',
    -- Time analysis stored as JSON (computed once on submit)
    -- Example: {"avg_per_question": 72, "fastest": {"q_no": 3, "seconds": 15},
    --           "slowest": {"q_no": 47, "seconds": 220}}
    time_analysis JSONB DEFAULT '{}',
    -- Recommendations array (generated on submit)
    -- Example: ["Practice more Fraction problems — scored 40%"]
    recommendations JSONB DEFAULT '[]',
    -- IP and device info (for admin fraud detection)
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- Responses: one row per question in the attempt
-- This is the most frequently written table during exam
CREATE TABLE responses (
    id BIGSERIAL PRIMARY KEY,
    attempt_id UUID NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
    question_id INT NOT NULL REFERENCES questions(id),
    question_no SMALLINT NOT NULL,
    -- denormalized for fast sorting
    -- Student's answer (NULL = not answered / skipped)
    selected_option SMALLINT CHECK (
        selected_option BETWEEN 1 AND 4
    ),
    -- Computed on submit (NULL during exam)
    is_correct BOOLEAN,
    marks_obtained SMALLINT DEFAULT 0,
    -- Timing (set when student saves answer)
    first_visited_at TIMESTAMPTZ,
    answered_at TIMESTAMPTZ,
    time_taken_seconds SMALLINT,
    -- Exam palette state — drives color coding in question grid
    -- gray=not visited, white=visited unanswered, green=answered,
    -- orange=marked+unanswered, purple=marked+answered
    visit_count SMALLINT DEFAULT 0,
    is_marked_review BOOLEAN DEFAULT false,
    UNIQUE(attempt_id, question_id)
);
-- ============================================================
-- LAYER 5: ADMIN, ANALYTICS & SUPPORT
-- ============================================================
-- Per-question rolling statistics
-- Updated by trigger after each attempt submission
-- Enables admin to see real difficulty without expensive aggregations
CREATE TABLE question_stats (
    question_id INT PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
    total_attempts INT DEFAULT 0,
    correct_count INT DEFAULT 0,
    wrong_count INT DEFAULT 0,
    skip_count INT DEFAULT 0,
    avg_time_seconds NUMERIC(6, 2) DEFAULT 0,
    -- actual difficulty: wrong_count / total_attempts (0.0 = easy, 1.0 = very hard)
    actual_difficulty NUMERIC(4, 3) DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Exam-level statistics cache
CREATE TABLE exam_stats (
    exam_id INT PRIMARY KEY REFERENCES exams(id) ON DELETE CASCADE,
    total_attempts INT DEFAULT 0,
    avg_score NUMERIC(5, 2) DEFAULT 0,
    avg_percentage NUMERIC(5, 2) DEFAULT 0,
    highest_score SMALLINT DEFAULT 0,
    pass_count INT DEFAULT 0,
    -- percentage >= 50
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Website enquiries / contact form
CREATE TABLE enquiries (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    school_name TEXT,
    district TEXT,
    std_class SMALLINT,
    message TEXT,
    -- For admin follow-up
    status enquiry_status DEFAULT 'new',
    admin_notes TEXT,
    responded_by UUID REFERENCES user_profiles(id),
    responded_at TIMESTAMPTZ,
    -- Source tracking
    source TEXT DEFAULT 'website',
    -- 'website', 'app', 'referral'
    referral_code TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- Notifications sent to students/parents
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    -- e.g. 'exam_assigned', 'attempt_submitted', 'exam_reminder', 'result_ready'
    title_en TEXT NOT NULL,
    title_mr TEXT,
    body_en TEXT,
    body_mr TEXT,
    -- Deep link data (what to open when notification is tapped)
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- ============================================================
-- INDEXES — Performance optimization
-- ============================================================
-- Question retrieval by exam (most common query)
CREATE INDEX idx_questions_exam_id ON questions(exam_id);
CREATE INDEX idx_questions_exam_question_no ON questions(exam_id, question_no);
CREATE INDEX idx_questions_section_id ON questions(section_id);
CREATE INDEX idx_questions_topic_id ON questions(topic_id);
CREATE INDEX idx_questions_context_id ON questions(context_id);
-- Options retrieval
CREATE INDEX idx_options_question_id ON options(question_id);
-- Attempt lookups (dashboard + admin)
CREATE INDEX idx_attempts_student_id ON attempts(student_id);
CREATE INDEX idx_attempts_exam_id ON attempts(exam_id);
CREATE INDEX idx_attempts_student_exam ON attempts(student_id, exam_id);
CREATE INDEX idx_attempts_status ON attempts(status);
CREATE INDEX idx_attempts_submitted_at ON attempts(submitted_at DESC);
-- Response lookups (most written table during exam)
CREATE INDEX idx_responses_attempt_id ON responses(attempt_id);
CREATE INDEX idx_responses_question_id ON responses(question_id);
-- Assignment lookups
CREATE INDEX idx_assignments_student_id ON exam_assignments(student_id);
CREATE INDEX idx_assignments_exam_id ON exam_assignments(exam_id);
-- Parent-student queries
CREATE INDEX idx_parent_student_parent_id ON parent_student_links(parent_id);
CREATE INDEX idx_parent_student_student_id ON parent_student_links(student_id);
-- Notification inbox
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read)
WHERE is_read = false;
-- Full-text search on questions (for admin question search)
CREATE INDEX idx_questions_text_search ON questions USING gin(to_tsvector('english', COALESCE(text_en, '')));
-- ============================================================
-- TRIGGERS
-- ============================================================
-- Auto-update updated_at on questions
CREATE OR REPLACE FUNCTION update_updated_at() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW();
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER questions_updated_at BEFORE
UPDATE ON questions FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER user_profiles_updated_at BEFORE
UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at();
-- Sync options.is_correct with questions.correct_option
-- So is_correct on options is always accurate
CREATE OR REPLACE FUNCTION sync_correct_option() RETURNS TRIGGER AS $$ BEGIN
UPDATE options
SET is_correct = (option_no = NEW.correct_option)
WHERE question_id = NEW.id;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER sync_correct_option_trigger
AFTER
INSERT
    OR
UPDATE OF correct_option ON questions FOR EACH ROW EXECUTE FUNCTION sync_correct_option();
-- Update question_stats after attempt submission
CREATE OR REPLACE FUNCTION update_question_stats_on_submit() RETURNS TRIGGER AS $$ BEGIN -- Only update when attempt moves to 'submitted'
    IF NEW.status = 'submitted'
    AND OLD.status = 'ongoing' THEN
INSERT INTO question_stats (
        question_id,
        total_attempts,
        correct_count,
        wrong_count,
        skip_count,
        avg_time_seconds
    )
SELECT r.question_id,
    COUNT(*),
    SUM(
        CASE
            WHEN r.is_correct = true THEN 1
            ELSE 0
        END
    ),
    SUM(
        CASE
            WHEN r.is_correct = false
            AND r.selected_option IS NOT NULL THEN 1
            ELSE 0
        END
    ),
    SUM(
        CASE
            WHEN r.selected_option IS NULL THEN 1
            ELSE 0
        END
    ),
    AVG(COALESCE(r.time_taken_seconds, 0))
FROM responses r
WHERE r.attempt_id = NEW.id
GROUP BY r.question_id ON CONFLICT (question_id) DO
UPDATE
SET total_attempts = question_stats.total_attempts + EXCLUDED.total_attempts,
    correct_count = question_stats.correct_count + EXCLUDED.correct_count,
    wrong_count = question_stats.wrong_count + EXCLUDED.wrong_count,
    skip_count = question_stats.skip_count + EXCLUDED.skip_count,
    avg_time_seconds = (
        (
            question_stats.avg_time_seconds * question_stats.total_attempts + EXCLUDED.avg_time_seconds * EXCLUDED.total_attempts
        ) / NULLIF(
            question_stats.total_attempts + EXCLUDED.total_attempts,
            0
        )
    ),
    actual_difficulty = CASE
        WHEN (
            question_stats.total_attempts + EXCLUDED.total_attempts
        ) > 0 THEN (
            question_stats.wrong_count + EXCLUDED.wrong_count
        )::NUMERIC / (
            question_stats.total_attempts + EXCLUDED.total_attempts
        )
        ELSE 0
    END,
    updated_at = NOW();
END IF;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER update_question_stats_trigger
AFTER
UPDATE OF status ON attempts FOR EACH ROW EXECUTE FUNCTION update_question_stats_on_submit();
-- Auto-create user_profile when new user signs up via Supabase Auth
-- Works for Email, Google, and Facebook sign-ups
CREATE OR REPLACE FUNCTION handle_new_auth_user() RETURNS TRIGGER AS $$
DECLARE v_provider TEXT;
v_name TEXT;
BEGIN -- Detect auth provider from Supabase metadata
v_provider := COALESCE(
    NEW.raw_app_meta_data->>'provider',
    'email'
);
-- Get name from OAuth provider metadata or fallback
v_name := COALESCE(
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'name',
    split_part(NEW.email, '@', 1)
);
INSERT INTO user_profiles (id, full_name, auth_provider)
VALUES (NEW.id, v_name, v_provider) ON CONFLICT (id) DO NOTHING;
RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
CREATE TRIGGER on_auth_user_created
AFTER
INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION handle_new_auth_user();
-- Update attempts_used counter in exam_assignments
CREATE OR REPLACE FUNCTION increment_attempts_used() RETURNS TRIGGER AS $$ BEGIN IF NEW.status = 'submitted'
    AND OLD.status = 'ongoing' THEN
UPDATE exam_assignments
SET attempts_used = attempts_used + 1
WHERE exam_id = NEW.exam_id
    AND student_id = NEW.student_id;
END IF;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER increment_attempts_used_trigger
AFTER
UPDATE OF status ON attempts FOR EACH ROW EXECUTE FUNCTION increment_attempts_used();
-- ============================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================
-- Enable RLS on all tables, then define who can access what
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE parent_student_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE exam_boards ENABLE ROW LEVEL SECURITY;
ALTER TABLE exam_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE exam_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE exams ENABLE ROW LEVEL SECURITY;
ALTER TABLE sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_contexts ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE options ENABLE ROW LEVEL SECURITY;
ALTER TABLE exam_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE enquiries ENABLE ROW LEVEL SECURITY;
-- Helper: check if current user has admin-level role
CREATE OR REPLACE FUNCTION is_admin() RETURNS BOOLEAN AS $$
SELECT EXISTS (
        SELECT 1
        FROM user_profiles
        WHERE id = auth.uid()
            AND role IN ('exam_admin', 'super_admin')
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;
-- Helper: check if user is a parent
CREATE OR REPLACE FUNCTION is_parent() RETURNS BOOLEAN AS $$
SELECT EXISTS (
        SELECT 1
        FROM user_profiles
        WHERE id = auth.uid()
            AND role = 'parent'
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;
-- Helper: check if parent_id can see student_id data
CREATE OR REPLACE FUNCTION parent_can_see_student(p_student_id UUID) RETURNS BOOLEAN AS $$
SELECT EXISTS (
        SELECT 1
        FROM parent_student_links
        WHERE parent_id = auth.uid()
            AND student_id = p_student_id
            AND is_active = true
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;
-- ── user_profiles ──
CREATE POLICY "Users read own profile" ON user_profiles FOR
SELECT USING (id = auth.uid());
CREATE POLICY "Users update own profile" ON user_profiles FOR
UPDATE USING (id = auth.uid());
CREATE POLICY "Parents read linked children profiles" ON user_profiles FOR
SELECT USING (parent_can_see_student(id));
CREATE POLICY "Admins read all profiles" ON user_profiles FOR ALL USING (is_admin());
-- ── exams & catalog (public read if active) ──
CREATE POLICY "Anyone reads active exams" ON exams FOR
SELECT USING (is_active = true);
CREATE POLICY "Admins manage exams" ON exams FOR ALL USING (is_admin());
CREATE POLICY "Anyone reads exam boards" ON exam_boards FOR
SELECT USING (is_active = true);
CREATE POLICY "Anyone reads active exam events" ON exam_events FOR
SELECT USING (is_active = true);
CREATE POLICY "Anyone reads sections" ON sections FOR
SELECT USING (true);
CREATE POLICY "Anyone reads topics" ON topics FOR
SELECT USING (true);
-- ── questions (read only if exam is active, correct_option hidden during exam via API) ──
CREATE POLICY "Anyone reads questions for active exams" ON questions FOR
SELECT USING (
        EXISTS (
            SELECT 1
            FROM exams
            WHERE id = exam_id
                AND is_active = true
        )
    );
CREATE POLICY "Admins manage questions" ON questions FOR ALL USING (is_admin());
CREATE POLICY "Anyone reads options" ON options FOR
SELECT USING (true);
CREATE POLICY "Anyone reads question contexts" ON question_contexts FOR
SELECT USING (true);
-- ── attempts (students see own, parents see children's) ──
CREATE POLICY "Students read own attempts" ON attempts FOR
SELECT USING (student_id = auth.uid());
CREATE POLICY "Students create own attempts" ON attempts FOR
INSERT WITH CHECK (student_id = auth.uid());
CREATE POLICY "Students update own ongoing attempts" ON attempts FOR
UPDATE USING (
        student_id = auth.uid()
        AND status = 'ongoing'
    );
CREATE POLICY "Parents read linked children attempts" ON attempts FOR
SELECT USING (parent_can_see_student(student_id));
CREATE POLICY "Admins read all attempts" ON attempts FOR ALL USING (is_admin());
-- ── responses ──
CREATE POLICY "Students manage own responses" ON responses FOR ALL USING (
    EXISTS (
        SELECT 1
        FROM attempts
        WHERE id = attempt_id
            AND student_id = auth.uid()
    )
);
CREATE POLICY "Parents read children responses" ON responses FOR
SELECT USING (
        EXISTS (
            SELECT 1
            FROM attempts a
            WHERE a.id = attempt_id
                AND parent_can_see_student(a.student_id)
        )
    );
-- ── exam_assignments ──
CREATE POLICY "Students read own assignments" ON exam_assignments FOR
SELECT USING (student_id = auth.uid());
CREATE POLICY "Parents read children assignments" ON exam_assignments FOR
SELECT USING (parent_can_see_student(student_id));
CREATE POLICY "Admins manage assignments" ON exam_assignments FOR ALL USING (is_admin());
-- ── notifications ──
CREATE POLICY "Users read own notifications" ON notifications FOR ALL USING (user_id = auth.uid());
-- ── enquiries (anyone can submit, only admins can read) ──
CREATE POLICY "Anyone can submit enquiry" ON enquiries FOR
INSERT WITH CHECK (true);
CREATE POLICY "Admins manage enquiries" ON enquiries FOR ALL USING (is_admin());
-- ── parent_student_links ──
CREATE POLICY "Parents manage their own links" ON parent_student_links FOR ALL USING (parent_id = auth.uid());
CREATE POLICY "Students see who linked them" ON parent_student_links FOR
SELECT USING (student_id = auth.uid());
CREATE POLICY "Admins manage all links" ON parent_student_links FOR ALL USING (is_admin());
-- ============================================================
-- SEED DATA: Initial board + exam structure
-- ============================================================
-- Exam Board
INSERT INTO exam_boards (name_en, name_mr, short_code, state)
VALUES (
        'Maharashtra State Council of Examinations',
        'महाराष्ट्र राज्य परीक्षा परिषद',
        'MSCE',
        'Maharashtra'
    );
-- Exam Category
INSERT INTO exam_categories (board_id, name_en, name_mr, description_en)
VALUES (
        1,
        'Pre-Upper Primary Scholarship',
        'पूर्व उच्च प्राथमिक शिष्यवृत्ती',
        'Scholarship exam for Std. 5th students'
    );
-- Exam Event
INSERT INTO exam_events (
        board_id,
        category_id,
        title_en,
        title_mr,
        std_class,
        year,
        exam_date
    )
VALUES (
        1,
        1,
        'Pre-Upper Primary Scholarship Examination 2025',
        'पूर्व उच्च प्राथमिक शिष्यवृत्ती परीक्षा 2025',
        5,
        2025,
        '2025-02-01'
    );
-- Paper I (0501)
INSERT INTO exams (
        event_id,
        paper_code,
        set_code,
        paper_number,
        title_en,
        title_mr,
        medium,
        instructions_en
    )
VALUES (
        1,
        '501',
        'A',
        1,
        'Paper I — First Language & Mathematics',
        'पेपर I — प्रथम भाषा व गणित',
        'english',
        'This question paper contains two sections. Section I: Q1–25 (First Language/English). Section II: Q26–75 (Mathematics). All 75 questions compulsory. 2 marks each. 90 minutes.'
    );
-- Paper II (0502)
INSERT INTO exams (
        event_id,
        paper_code,
        set_code,
        paper_number,
        title_en,
        title_mr,
        medium,
        instructions_en
    )
VALUES (
        1,
        '502',
        'A',
        2,
        'Paper II — Third Language & Intelligence Test',
        'पेपर II — तृतीय भाषा व बुद्धिमत्ता चाचणी',
        'english',
        'This question paper contains two sections. Section I: Q1–25 (Third Language/Marathi). Section II: Q26–75 (Intelligence Test). All 75 questions compulsory. 2 marks each. 90 minutes.'
    );
-- Sections for Paper I (exam_id = 1)
INSERT INTO sections (
        exam_id,
        section_label,
        subject_en,
        subject_mr,
        question_from,
        question_to,
        order_index,
        color_hex
    )
VALUES (
        1,
        'I',
        'English',
        'इंग्रजी',
        1,
        25,
        1,
        '#3B82F6'
    ),
    (
        1,
        'II',
        'Mathematics',
        'गणित',
        26,
        75,
        2,
        '#10B981'
    );
-- Sections for Paper II (exam_id = 2)
INSERT INTO sections (
        exam_id,
        section_label,
        subject_en,
        subject_mr,
        question_from,
        question_to,
        order_index,
        color_hex
    )
VALUES (
        2,
        'I',
        'Marathi',
        'मराठी',
        1,
        25,
        1,
        '#F59E0B'
    ),
    (
        2,
        'II',
        'Intelligence Test',
        'बुद्धिमत्ता चाचणी',
        26,
        75,
        2,
        '#8B5CF6'
    );
-- Topics for Paper I - English (section_id = 1)
INSERT INTO topics (section_id, name_en, name_mr, order_index)
VALUES (1, 'Reading Comprehension', 'गद्य आकलन', 1),
    (1, 'Poetry', 'पद्य आकलन', 2),
    (1, 'Advertisement Reading', 'जाहिरात वाचन', 3),
    (1, 'Grammar', 'व्याकरण', 4),
    (1, 'Vocabulary', 'शब्दसंपत्ती', 5),
    (1, 'Picture Comprehension', 'चित्र आकलन', 6);
-- Topics for Paper I - Mathematics (section_id = 2)
INSERT INTO topics (section_id, name_en, name_mr, order_index)
VALUES (2, 'Weights and Measures', 'वजन आणि मापे', 1),
    (2, 'Fractions', 'अपूर्णांक', 2),
    (2, 'Profit and Loss', 'नफा-तोटा', 3),
    (2, 'Simple Interest', 'साधे व्याज', 4),
    (2, 'Geometry', 'भूमिती', 5),
    (2, 'Percentages', 'टक्केवारी', 6),
    (2, 'Time and Distance', 'वेळ आणि अंतर', 7),
    (2, 'Number System', 'संख्या प्रणाली', 8),
    (2, 'Data Handling', 'माहितीचे व्यवस्थापन', 9),
    (2, 'Algebra', 'बीजगणित', 10),
    (
        2,
        'Calendar and Clock',
        'दिनदर्शिका आणि घड्याळ',
        11
    );
-- Topics for Paper II - Marathi (section_id = 3)
INSERT INTO topics (section_id, name_en, name_mr, order_index)
VALUES (3, 'Vocabulary', 'शब्दसंपत्ती', 1),
    (3, 'Grammar', 'व्याकरण', 2),
    (3, 'Reading Comprehension', 'गद्य आकलन', 3),
    (3, 'Poetry', 'पद्य आकलन', 4),
    (
        3,
        'Idioms and Proverbs',
        'म्हणी आणि वाक्प्रचार',
        5
    );
-- Topics for Paper II - Intelligence Test (section_id = 4)
INSERT INTO topics (section_id, name_en, name_mr, order_index)
VALUES (
        4,
        'Mirror and Water Images',
        'आरसा आणि पाणी प्रतिमा',
        1
    ),
    (
        4,
        'Analogy',
        'साधर्म्य',
        2
    ),
    (
        4,
        'Series Completion',
        'मालिका पूर्तता',
        3
    ),
    (
        4,
        'Pattern Recognition',
        'आकृती ओळख',
        4
    ),
    (
        4,
        'Direction and Position',
        'दिशा आणि स्थान',
        5
    ),
    (
        4,
        'Coding and Decoding',
        'कूटलेखन',
        6
    ),
    (
        4,
        'Venn Diagrams',
        'वेन आकृत्या',
        7
    ),
    (
        4,
        'Number Puzzles',
        'संख्या कोडे',
        8
    ),
    (
        4,
        'Odd One Out',
        'वेगळी वस्तू ओळखा',
        9
    ),
    (
        4,
        'Logic and Reasoning',
        'तर्क आणि विचारशक्ती',
        10
    );
-- Initialize question_stats and exam_stats for seeded exams
INSERT INTO exam_stats (exam_id)
VALUES (1),
    (2);
-- ============================================================
-- VIEWS — Convenient query interfaces for API
-- ============================================================
-- View: full question with section and topic names (for exam taking)
CREATE VIEW v_exam_questions AS
SELECT q.id,
    q.exam_id,
    q.section_id,
    q.topic_id,
    q.context_id,
    q.question_no,
    q.question_type,
    q.text_en,
    q.text_mr,
    q.question_image_url,
    q.question_image_alt_en,
    q.question_image_alt_mr,
    q.marks,
    q.difficulty,
    q.tags,
    -- NOTE: correct_option and explanation are intentionally EXCLUDED
    -- from this view — the API uses this view for exam delivery
    -- Correct answer only exposed via v_exam_answers (admin/analysis only)
    s.subject_en AS section_subject_en,
    s.subject_mr AS section_subject_mr,
    s.section_label,
    t.name_en AS topic_name_en,
    t.name_mr AS topic_name_mr,
    qc.context_type,
    qc.content_en AS context_content_en,
    qc.content_mr AS context_content_mr,
    qc.title_en AS context_title_en,
    qc.title_mr AS context_title_mr,
    qc.image_url AS context_image_url,
    qc.instruction_en AS context_instruction_en,
    qc.instruction_mr AS context_instruction_mr,
    qc.applies_from AS context_applies_from,
    qc.applies_to AS context_applies_to
FROM questions q
    LEFT JOIN sections s ON s.id = q.section_id
    LEFT JOIN topics t ON t.id = q.topic_id
    LEFT JOIN question_contexts qc ON qc.id = q.context_id;
-- View: answers + explanations (for post-exam review ONLY)
CREATE VIEW v_exam_answers AS
SELECT q.id AS question_id,
    q.exam_id,
    q.question_no,
    q.correct_option,
    q.explanation_en,
    q.explanation_mr,
    q.hint_en,
    q.hint_mr
FROM questions q;
-- View: student attempt summary (for dashboard)
CREATE VIEW v_student_attempts AS
SELECT a.id AS attempt_id,
    a.student_id,
    a.exam_id,
    a.attempt_number,
    a.status,
    a.started_at,
    a.submitted_at,
    a.duration_seconds,
    a.total_score,
    a.total_correct,
    a.total_wrong,
    a.total_skipped,
    a.percentage,
    a.grade,
    e.paper_code,
    e.title_en AS exam_title_en,
    e.title_mr AS exam_title_mr,
    e.total_marks,
    ee.std_class,
    ee.year AS exam_year
FROM attempts a
    JOIN exams e ON e.id = a.exam_id
    JOIN exam_events ee ON ee.id = e.event_id;
-- ============================================================
-- COMMENTS — Documentation for each table
-- ============================================================
COMMENT ON TABLE exam_boards IS 'Exam boards/organizations (MSCE, CBSE, SSC). Scale to multiple boards.';
COMMENT ON TABLE exam_categories IS 'Categories under a board (Scholarship, Board Exam, Entrance).';
COMMENT ON TABLE exam_events IS 'Annual exam event grouping all papers (e.g. MSCE Scholarship 2025).';
COMMENT ON TABLE exams IS 'Individual exam papers (Paper I = 501, Paper II = 502).';
COMMENT ON TABLE sections IS 'Sections within a paper (Section I = Language, Section II = Math).';
COMMENT ON TABLE topics IS 'Sub-topics for analysis (Grammar, Fractions, Mirror Images).';
COMMENT ON TABLE question_contexts IS 'Shared context (passage/poem/figure) referenced by multiple questions.';
COMMENT ON TABLE questions IS 'Core question bank. text_en/text_mr for multilingual. Add text_hi for Hindi.';
COMMENT ON TABLE options IS '4 options per question. Supports text, image, or both.';
COMMENT ON TABLE user_profiles IS 'Extends Supabase auth.users. Role-based (student/parent/admin). Auto-created by trigger.';
COMMENT ON TABLE parent_student_links IS 'Parent can monitor multiple children. Child can have multiple parents.';
COMMENT ON TABLE exam_assignments IS 'Which exams are assigned to which students. Includes practice and admin-assigned.';
COMMENT ON TABLE attempts IS 'One exam session. Scores computed and stored as JSON on submit for fast reads.';
COMMENT ON TABLE responses IS 'One row per question per attempt. Most written table during exam.';
COMMENT ON TABLE question_stats IS 'Rolling statistics per question. Updated by trigger. No expensive aggregations.';
COMMENT ON TABLE exam_stats IS 'Rolling exam-level statistics cache.';
COMMENT ON TABLE enquiries IS 'Contact form submissions from landing page.';
COMMENT ON TABLE notifications IS 'In-app notifications for students and parents.';
COMMENT ON COLUMN questions.text_en IS 'English question text. NULL for image_only questions.';
COMMENT ON COLUMN questions.text_mr IS 'Marathi question text. NULL for English-only questions. Add text_hi for Hindi.';
COMMENT ON COLUMN questions.correct_option IS 'Correct option number 1-4. NEVER sent to frontend during active exam.';
COMMENT ON COLUMN questions.explanation_en IS 'Post-exam explanation of why the answer is correct.';
COMMENT ON COLUMN questions.actual_difficulty_ratio IS '0.0=easy, 1.0=very hard. Computed from real student data.';
COMMENT ON COLUMN attempts.section_scores IS 'JSON: computed once on submit. [{section_id, label, score, total, percentage}]';
COMMENT ON COLUMN attempts.topic_scores IS 'JSON: computed once on submit. [{topic_id, name, correct, total, status}]';
COMMENT ON COLUMN attempts.time_analysis IS 'JSON: computed once on submit. {avg_per_question, fastest, slowest}';
COMMENT ON COLUMN responses.is_marked_review IS 'Orange flag in question palette. Student marked for later review.';
-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
-- Tables created: 18
-- Indexes created: 12
-- Triggers created: 5
-- RLS Policies: 20+
-- Views: 3
-- Seed data: 1 board, 1 category, 1 event, 2 exams, 4 sections, 26 topics
-- ============================================================