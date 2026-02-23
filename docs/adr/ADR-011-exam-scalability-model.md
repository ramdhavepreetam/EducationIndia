# ADR-011: Exam Scalability Model

**Date:** 2025-02-21
**Status:** Accepted
**Decider:** Preetam
**Modules Affected:** catalog, question, admin (exam creation)

---

## Context

ScholarPath launches with one exam (MSCE 5th Std Paper I + II, 2025).
The product vision is to grow to: 8th Std scholarship, multiple years of
previous papers, potentially CBSE or other boards, and eventually custom
practice tests. The catalog data model must accommodate this growth without
schema changes. Question import must work for any exam, not just MSCE 2025.
The admin must be able to publish new exams without code deployments.

---

## Decision

We will use a 4-level exam hierarchy: exam_boards → exam_categories →
exam_events → exams. Each new exam type is a data operation only — insert
rows, import questions, set is_active = true. No code changes required.
New exam years = new exam_event row. New boards (CBSE) = new exam_board row.
The question import JSON format is exam-agnostic (takes exam_id as parameter).

---

## Alternatives Considered

### Option 1: Flat exam table with type/board columns
Single exams table with board VARCHAR, type VARCHAR, year INT columns.
- Pro: Simple — one table to query
- Con: Filtering becomes complex: WHERE board='MSCE' AND type='scholarship' AND class=5
- Con: Adding new board means hoping VARCHAR values are consistent
- Con: No place for board-level metadata (logo, website, description)

### Option 2: Hardcode MSCE structure, migrate later
Build specifically for MSCE 5th std, redesign when adding new exams.
- Pro: Fastest initial implementation
- Con: Migrations on a live database with student data are risky
- Con: The 4-level hierarchy adds only 3 extra tables — minimal cost now

### Option 3: 4-level hierarchy ← CHOSEN
exam_boards → exam_categories → exam_events → exams
- Pro: Adding CBSE = insert exam_board row + categories + events + exams
- Pro: "Previous year papers" = multiple exam_events rows under same category
- Pro: Admin can manage exams via data, not code
- Con: Slightly more JOIN depth for exam listing queries

---

## Consequences

### Positive
- Adding 2026 MSCE papers = 1 exam_event row + 2 exam rows + import questions
- Adding 8th Std = 1 exam_category row + exam hierarchy below it
- Previous year papers section: query exam_events WHERE category_id=1 ORDER BY year DESC
- Admin panel shows exam hierarchy — easy to navigate

### Negative
- 4-level JOIN for "get all exams with board name" — acceptable, indexed
- Admin UI needs to understand hierarchy (create board → category → event → exam)

### Neutral
- is_active flag at exam level — admin controls what students see
- exam_events.exam_date allows "upcoming exam" countdown feature
- Different exam boards may have different marks-per-question — stored at exam level

---

## Module Impact

```
catalog/models.py      → All 4 hierarchy tables
catalog/service.py     → list_exams() accepts board_id, category_id filters
catalog/router.py      → GET /api/catalog/exams?board=MSCE&class=5&year=2025
admin/router.py        → POST /api/admin/exams (create any level of hierarchy)
question/importer.py   → JSON import takes exam_id — works for any exam
seed.py                → Seeds MSCE 2025 as reference data
```

---

## Implementation Notes

Adding a new exam year (pure data operation):
```sql
-- Step 1: New event for 2026
INSERT INTO exam_events (board_id, category_id, title_en, std_class, year, exam_date)
VALUES (1, 1, 'Pre-Upper Primary Scholarship 2026', 5, 2026, '2026-02-01');

-- Step 2: New papers
INSERT INTO exams (event_id, paper_code, ...) VALUES (...);

-- Step 3: Bulk import questions via admin API
POST /api/admin/questions/bulk-import
{ "exam_id": 3, "questions": [...] }

-- Step 4: Publish when ready
UPDATE exams SET is_active = true WHERE event_id = 3;
```

Adding a new board (CBSE):
```sql
INSERT INTO exam_boards (name_en, short_code, state)
VALUES ('Central Board of Secondary Education', 'CBSE', 'National');

INSERT INTO exam_categories (board_id, name_en)
VALUES (2, 'Class 10 Board Examination');
-- Then exam_events and exams as above
```

Admin exam listing API response shape:
```json
{
  "board": "MSCE",
  "category": "Pre-Upper Primary Scholarship",
  "events": [
    {
      "year": 2025,
      "std_class": 5,
      "papers": [
        { "id": 1, "paper_code": "501", "title_en": "Paper I", "is_active": true },
        { "id": 2, "paper_code": "502", "title_en": "Paper II", "is_active": true }
      ]
    }
  ]
}
```

---

## Review Trigger

Revisit when adding custom practice tests (admin creates ad-hoc question sets
not tied to real exam papers) — that may need a different structure than the
real-exam hierarchy. Revisit if competitive exam types (like JEE/NEET style)
with negative marking are added — marking scheme stored at exam level.
