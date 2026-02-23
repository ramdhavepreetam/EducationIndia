# Catalog Module

Owns the 4-level exam hierarchy (ADR-011):
`exam_boards → exam_categories → exam_events → exams`

Also owns: `sections`, `topics` (per-exam structure used by question + analysis modules).

---

## Ownership

| Table | Description |
|-------|-------------|
| `exam_boards` | Top-level board (MSCE, CBSE) |
| `exam_categories` | Category within a board (5th Std Scholarship) |
| `exam_events` | A specific year/edition (MSCE 2025, MSCE 2026) |
| `exams` | A single paper (Paper I, Paper II) |
| `sections` | Sections within a paper (Section I: English, Section II: Maths) |
| `topics` | Topics within a section (Grammar, Fractions, Mirror Images) |

---

## Public API (consumed by other modules)

```python
from app.modules.catalog.service import catalog_service

# Used by attempt module to validate exam before starting
exam = await catalog_service.get_active_exam(db, exam_id)

# Used by question module to validate exam_id exists
exam = await catalog_service.get_exam(db, exam_id)

# Used by analysis module to get section/topic structure
exams = await catalog_service.list_exams(db)
```

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/catalog/boards` | Public | List all active boards |
| GET | `/api/catalog/exams` | Public | List exams (filters: board_id, std_class, year) |
| GET | `/api/catalog/exams/{id}` | Public | Single exam with sections + topics |
| PUT | `/api/catalog/exams/{id}/publish` | Admin | Set is_active=True |

---

## Multilingual Pattern (ADR-003)

All user-facing text fields have both `_en` and `_mr` variants:
- `name_en` / `name_mr`
- `title_en` / `title_mr`
- `subject_en` / `subject_mr`

API **always returns both** columns. The frontend decides which to display.
`NULL` means that language version doesn't exist (acceptable for some fields).

---

## Adding a New Exam Year (Pure Data — No Code Change)

```sql
-- 1. New event
INSERT INTO exam_events (board_id, category_id, title_en, std_class, year, exam_date)
VALUES (1, 1, 'Pre-Upper Primary Scholarship 2026', 5, 2026, '2026-02-01');

-- 2. New papers
INSERT INTO exams (event_id, paper_code, title_en, ...)
VALUES (3, '501', 'Paper I', ...);

-- 3. Bulk import questions via admin API
-- POST /api/admin/questions/bulk-import { "exam_id": 3, "questions": [...] }

-- 4. Publish when ready
PUT /api/catalog/exams/{id}/publish
```

---

## Module Boundary Rules

- **Exposes**: `catalog_service.get_exam()`, `catalog_service.get_active_exam()`, `catalog_service.list_exams()`
- **Consumes**: Auth module (`require_admin` dependency only)
- **Never**: Direct DB queries in router or service. All queries in `repository.py`.
- **Never**: Business logic in admin module — admin delegates to catalog_service.
