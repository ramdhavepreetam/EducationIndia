# Question Module

Owns: `question_contexts`, `questions`, `options`

## Purpose

Stores and serves exam questions. This module has the most critical security
boundary in the entire application — **correct_option must never be returned
during an active exam session** (ADR-012).

## Public Interface

Other modules consume these methods only. Never import from internal files.

```python
from app.modules.question.service import question_service

# Delivery (no correct_option) — used by attempt module
questions = await question_service.get_questions_for_exam(db, exam_id)

# Review (with correct_option) — only after attempt is submitted
question  = await question_service.get_question_for_review(db, question_id, attempt_id, student_id)
```

## Security Architecture (ADR-012)

Double-enforcement of the answer security boundary:

| Layer | Mechanism |
|---|---|
| Database | `v_exam_questions` view excludes `correct_option` and `explanation` columns |
| Pydantic | `QuestionDeliverySchema` does not declare `correct_option` field |
| Service | `get_question_for_review()` checks `attempt.status == 'submitted'` before returning answers |
| Tests | `test_security.py` verifies schema fields, JSON output, and attempt status gating |

**If you add `correct_option` to `QuestionDeliverySchema`, `test_security.py` will fail.**

## Schema Hierarchy

```
QuestionDeliverySchema  → active exam       | no correct_option, no explanation
QuestionReviewSchema    → after submission  | + correct_option, + explanation
QuestionAdminSchema     → admin panel only  | + hints, + stats
BulkImportSchema        → import endpoint   | full data for inserting
```

## Endpoints

### Student-facing (`/api/questions`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/questions/?exam_id=1` | Any user | Delivery questions (no correct_option) |
| GET | `/api/questions/{id}/review?attempt_id=...` | Owner of attempt | Post-exam review |

### Admin (`/api/admin/questions`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/admin/questions/?exam_id=1` | exam_admin | Full admin question list |
| PUT | `/api/admin/questions/{id}` | exam_admin | Update question fields |
| POST | `/api/admin/questions/bulk-import` | exam_admin | Bulk import from JSON |
| DELETE | `/api/admin/questions/{id}` | super_admin | Hard delete |

## Question Types (ADR-004)

| Type | text_en | text_mr | image | context_ref | Options |
|------|---------|---------|-------|-------------|---------|
| `text` | Required | Optional | — | — | 4 × text_en |
| `text_image` | Required | Optional | Required | — | 4 × text_en |
| `image_only` | Must be None | Must be None | Required OR context_ref | Optional | 4 × image_url |
| `context_text` | Required | Optional | — | Required | 4 × text_en |
| `context_image` | — | — | — | Required | 4 × image_url |
| `marathi_only` | Must be None | Required | — | — | 4 × text_mr |
| `bilingual` | Required | Required | — | — | 4 × text_en |

## Bulk Import Format

```json
{
  "exam_id": 1,
  "contexts": [
    {
      "context_type": "paragraph",
      "content_en": "Read the passage and answer...",
      "applies_from": 1,
      "applies_to": 5
    }
  ],
  "questions": [
    {
      "section_id": 1,
      "topic_id": 3,
      "question_no": 1,
      "question_type": "context_text",
      "text_en": "Based on the passage, the author's main argument is...",
      "correct_option": 2,
      "context_ref": 0,
      "options": [
        { "option_no": 1, "text_en": "Option A" },
        { "option_no": 2, "text_en": "Option B" },
        { "option_no": 3, "text_en": "Option C" },
        { "option_no": 4, "text_en": "Option D" }
      ]
    }
  ]
}
```

`context_ref` is a 0-based index into the top-level `contexts` array.
The importer resolves these indices to real DB IDs during insertion.

## Adding Questions for a New Exam

1. Prepare JSON following the bulk import format above
2. Ensure `exam_id` exists in the DB
3. POST to `/api/admin/questions/bulk-import` with an admin JWT
4. Verify response: `{ "inserted": N, "skipped": 0, "errors": [] }`
5. Run `GET /api/questions/?exam_id=N` — should return `N` items, no `correct_option`

## Running Tests

```bash
# From project root:
DEBUG=true PYTHONPATH=backend backend/.venv/bin/pytest \
    backend/app/modules/question/tests/ -v

# Security tests only (run these before every deploy):
backend/.venv/bin/pytest backend/app/modules/question/tests/test_security.py -v
```
