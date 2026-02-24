# ScholarPath

Multilingual online exam preparation portal for Maharashtra MSCE Scholarship Examinations (5th and 8th standard).

---

## Tech Stack

| Layer     | Technology                                  |
|-----------|---------------------------------------------|
| Backend   | Python 3.11 + FastAPI + SQLAlchemy 2.0      |
| Database  | PostgreSQL via Supabase                     |
| Auth      | Supabase Auth (Email/Password + Google OAuth)|
| Frontend  | React 18 + Vite + Tailwind CSS + Zustand    |
| PDF       | jsPDF + html2canvas                         |

---

## Running the Project

### Backend

```bash
# From project root
DEBUG=true PYTHONPATH=backend backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

---

## User Roles & Login Guide

All roles share the **same login page**: `http://localhost:5173/login`

There is no separate login URL per role. The app reads the `role` field from your Supabase user profile and redirects accordingly.

---

### How to Log In as a Student

1. Go to `http://localhost:5173/login`
2. Enter email + password (or use Google OAuth)
3. If first time: complete the onboarding form at `/onboarding` (school name, district, class, medium)
4. You land at `/dashboard`

**What a student sees:**
- `/dashboard` — Available exams, attempt history, performance stats
- `/exam/:id/start` — Exam instructions page before starting
- `/exam/:id/attempt` — Live exam (timer + question palette + autosave)
- `/attempts/:id/result` — Score report with topic breakdown + PDF download

**Student role in DB:** `role = 'student'`

To create a student account in Supabase SQL Editor (after the user registers via the UI):
```sql
UPDATE user_profiles SET role = 'student' WHERE id = '<user-uuid>';
```

---

### How to Log In as Admin Panel

1. Go to `http://localhost:5173/login`
2. Log in with your admin account credentials
3. You land at `/dashboard` (same as students)
4. Click **Admin Panel** in the left sidebar — this link is **only visible to admins**
5. Or navigate directly to `http://localhost:5173/admin`

> Non-admin users who visit `/admin` directly see an **Access Denied** page, not an error.

**What an admin sees:**

| Route                  | Page                | Purpose                                      |
|------------------------|---------------------|----------------------------------------------|
| `/admin`               | Dashboard           | Platform stats: total students, attempts, exams, questions. Recent activity table. |
| `/admin/questions`     | Question Manager    | Browse all questions with correct answers visible. Edit text, difficulty, explanation. Bulk JSON import. |
| `/admin/publish`       | Exam Publisher      | List all exams (active + inactive). Publish/unpublish toggle. Publish is disabled until 75 questions are loaded. |
| `/admin/images`        | Image Uploader      | Upload images for Intelligence Test (image-only question types). |
| `/admin/stats`         | Question Stats      | Per-question performance data: attempts, correct %, difficulty score. CSV export. |

**Admin roles in DB:** `exam_admin` or `super_admin`

To grant admin access in Supabase SQL Editor:
```sql
-- Exam admin (can manage questions, exams, images, stats)
UPDATE user_profiles SET role = 'exam_admin' WHERE id = '<user-uuid>';

-- Super admin (full access)
UPDATE user_profiles SET role = 'super_admin' WHERE id = '<user-uuid>';
```

Or find a user by email first:
```sql
SELECT up.id, up.full_name, up.role
FROM user_profiles up
JOIN auth.users au ON au.id = up.id
WHERE au.email = 'admin@example.com';
```

---

### How to Log In as a Parent

1. Go to `http://localhost:5173/login`
2. Log in with your parent account credentials
3. Complete onboarding if first time
4. You land at `/dashboard`

> **Note:** The dedicated parent dashboard module is not yet built. Parents currently see the same student dashboard. The parent-specific features (viewing linked children, monitoring their results) are planned for a future sprint.

**Parent role in DB:** `role = 'parent'`

To set a user as parent in Supabase SQL Editor:
```sql
UPDATE user_profiles SET role = 'parent' WHERE id = '<user-uuid>';
```

To link a parent to a student (so the parent can view that child's data when the parent module is built):
```sql
INSERT INTO parent_student_links (parent_id, student_id, linked_by, child_nickname)
VALUES (
    '<parent-uuid>',
    '<student-uuid>',
    '<parent-uuid>',
    'My Child'
);
```

---

## Route Summary

| Route                        | Access         | Status         |
|------------------------------|----------------|----------------|
| `/login`                     | Public         | ✅ Built        |
| `/register`                  | Public         | ✅ Built        |
| `/onboarding`                | Auth required  | ✅ Built        |
| `/dashboard`                 | Auth required  | ✅ Built        |
| `/exam/:id/start`            | Auth required  | ✅ Built        |
| `/exam/:id/attempt`          | Auth required  | ✅ Built        |
| `/exam/submitted/:id`        | Auth required  | ✅ Built        |
| `/attempts/:id/result`       | Auth required  | ✅ Built        |
| `/admin`                     | Admin only     | ✅ Built        |
| `/admin/questions`           | Admin only     | ✅ Built        |
| `/admin/publish`             | Admin only     | ✅ Built        |
| `/admin/images`              | Admin only     | ✅ Built        |
| `/admin/stats`               | Admin only     | ✅ Built        |
| `/exams`                     | Auth required  | ⬜ Placeholder  |
| `/results`                   | Auth required  | ⬜ Placeholder  |
| `/profile`                   | Auth required  | ⬜ Placeholder  |
| `/parent`                    | Parent only    | ⬜ Not built    |

---

## Backend API Routes

| Method | Path                                  | Auth Required | Description                          |
|--------|---------------------------------------|---------------|--------------------------------------|
| GET    | `/api/users/me`                       | Any           | Current user profile                 |
| PUT    | `/api/users/me`                       | Any           | Update profile                       |
| POST   | `/api/users/me/complete-profile`      | Any           | Complete onboarding                  |
| GET    | `/api/catalog/exams`                  | Any           | List active exams                    |
| GET    | `/api/catalog/exams/{id}`             | Any           | Exam detail with sections + topics   |
| GET    | `/api/questions/`                     | Any           | Questions for exam (no correct answer)|
| GET    | `/api/questions/{id}/review`          | Student       | Question review (after submission)   |
| POST   | `/api/attempts/start`                 | Student       | Start new exam attempt               |
| POST   | `/api/attempts/{id}/save`             | Student       | Autosave response                    |
| POST   | `/api/attempts/{id}/submit`           | Student       | Submit exam + trigger scoring        |
| GET    | `/api/analysis/{attempt_id}`          | Student       | Full result report                   |
| POST   | `/api/media/upload`                   | Admin         | Upload question image                |
| GET    | `/api/admin/dashboard/overview`       | Admin         | Platform stats (4 counts)            |
| GET    | `/api/admin/dashboard/student`        | Student       | Student-specific dashboard data      |
| GET    | `/api/admin/dashboard/attempts/recent`| Admin         | Last 20 attempts all students        |
| GET    | `/api/admin/catalog/exams`            | Admin         | All exams with question count        |
| PUT    | `/api/admin/catalog/exams/{id}/publish`| Admin        | Publish exam                         |
| PUT    | `/api/admin/catalog/exams/{id}/unpublish`| Admin      | Unpublish exam                       |
| GET    | `/api/admin/questions/stats`          | Admin         | Per-question performance stats       |
| GET    | `/api/admin/questions/`              | Admin         | All questions with correct answers   |
| POST   | `/api/admin/questions/bulk-import`    | Admin         | Bulk JSON import                     |

---

## Checking What's in the Database

Use the Supabase SQL Editor or connect directly via your `DATABASE_URL`.

**Check all users and their roles:**
```sql
SELECT up.id, up.full_name, up.role, up.is_onboarded, au.email
FROM user_profiles up
JOIN auth.users au ON au.id = up.id
ORDER BY up.created_at DESC;
```

**Check student attempts:**
```sql
SELECT a.id, up.full_name, e.title_en, a.status, a.total_score, a.percentage, a.grade, a.submitted_at
FROM attempts a
JOIN user_profiles up ON up.id = a.student_id
JOIN exams e ON e.id = a.exam_id
ORDER BY a.started_at DESC;
```

**Check question counts per exam:**
```sql
SELECT e.id, e.title_en, e.is_active, COUNT(q.id) AS loaded, e.total_questions AS required
FROM exams e
LEFT JOIN questions q ON q.exam_id = e.id
GROUP BY e.id
ORDER BY e.id;
```

**Check parent-child links:**
```sql
SELECT
    p.full_name AS parent_name,
    s.full_name AS child_name,
    l.child_nickname,
    l.is_active
FROM parent_student_links l
JOIN user_profiles p ON p.id = l.parent_id
JOIN user_profiles s ON s.id = l.student_id;
```

---

## Environment Variables

Copy `.env.example` (if present) or create `.env` at the project root:

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@host/scholarpath
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret
MEDIA_PROVIDER=local

# Frontend (.env.local in /frontend)
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

---

## Module Build Status

| Module           | Backend   | Frontend  |
|------------------|-----------|-----------|
| auth             | ✅ Done    | ✅ Done    |
| user             | ✅ Done    | ⬜ Partial |
| catalog          | ✅ Done    | ⬜ Pending |
| question         | ✅ Done    | ✅ Done (admin) |
| attempt          | ✅ Done    | ✅ Done    |
| analysis         | ✅ Done    | ✅ Done    |
| media            | ✅ Done    | ✅ Done (admin) |
| admin            | ✅ Done    | ✅ Done    |
| dashboard        | ✅ Done    | ✅ Done    |
| parent           | ⬜ Planned | ⬜ Planned |
