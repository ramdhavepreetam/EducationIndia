# ADR-004: Question Content Model

**Date:** 2025-02-21
**Status:** Accepted
**Decider:** Preetam
**Modules Affected:** question, attempt (reading), analysis (reading correct answers)

---

## Context

Analysing the actual MSCE exam PDFs revealed far more question complexity than
a simple "text + 4 options" model. Questions fall into 7 distinct types. Some
questions share a passage (Q1-2 share Bal Gandharva paragraph). Some questions
are entirely images (Intelligence Test mirror/water image questions where both
the question AND all 4 options are figures with no text). Some questions are
Marathi-only with no English version. The content model must handle all of these
without creating separate tables per type, while remaining simple to bulk-import
from JSON and render correctly on the frontend.

---

## Decision

We will use a single `questions` table with a `question_type` enum that drives
rendering. Shared content (passages, poems, instructions) lives in
`question_contexts` table — referenced by multiple questions. Options live in
a separate `options` table supporting text, image, or both per option.
The `question_type` field is the contract between database and frontend:
the React component reads this field and renders accordingly.

---

## Alternatives Considered

### Option 1: One table per question type
table: text_questions, image_questions, passage_questions, etc.
- Pro: Pure schema — each table has only relevant columns
- Con: JOINs required to fetch a full paper (75 questions from 5+ tables)
- Con: Bulk import requires routing to correct table
- Con: API response shape differs per type — complex frontend handling

### Option 2: Single table with JSONB content column
questions(id, question_no, content JSONB, question_type)
content = {"text_en": "...", "options": [...], "image_url": "..."}
- Pro: Flexible — any structure fits in JSON
- Con: Loses all type safety and column-level indexing
- Con: ORM mapping is awkward
- Con: Admin interface cannot validate required fields per type

### Option 3: Single table + separate contexts + separate options ← CHOSEN
questions table + question_contexts table + options table
- Pro: One JOIN pattern for all question types
- Pro: Passage stored once, referenced by Q1 and Q2 (not duplicated)
- Pro: question_type drives frontend rendering — clean contract
- Pro: Options table handles text-only, image-only, or mixed per option
- Con: Three tables to manage instead of one

---

## Consequences

### Positive
- API always returns same JSON shape regardless of question type
- Frontend switch statement on question_type covers all rendering cases
- Intelligence Test questions (image options) work without schema changes
- Marathi-only questions: text_en = NULL, handled by get_text() fallback
- Passage stored once in question_contexts regardless of how many questions reference it

### Negative
- question_type enum must be extended for any new question format
- context_id being NULL (standalone question) vs NOT NULL (passage question)
  requires careful handling in API responses

### Neutral
- options.is_correct is redundant with questions.correct_option
  but kept for query convenience — synced by DB trigger
- question_image_url is for image embedded in question body (not context)
  vs question_contexts.image_url which is the shared context image

---

## Module Impact

```
question/models.py         → questions, options, question_contexts tables
question/schemas.py        → QuestionResponse always includes context if context_id set
question/service.py        → get_questions_for_exam() joins context when context_id != null
question/repository.py     → fetch_by_exam_id() with LEFT JOIN on question_contexts
question/importer.py       → bulk JSON import handles all 7 question_types
database migration         → sync_correct_option trigger keeps options.is_correct accurate
```

---

## Implementation Notes

question_type enum values and when to use each:
```
text           → Q6: "August is ___ month." + 4 text options
text_image     → Q33: "How many triangles in this figure?" + image in question
image_only     → Q27: Mirror image — image IS the question, all 4 options are images
context_text   → Q1-Q5: Share Bal Gandharva passage or "House Next Door" poem
context_image  → Q35-Q36: Share pictograph table as context
marathi_only   → Q1-Q25 in Paper 0502: text_mr only, text_en = NULL
bilingual      → Intelligence Test Q with both EN + MR text side by side
```

Bulk import JSON format for admin:
```json
{
  "exam_id": 1,
  "contexts": [
    {
      "context_type": "paragraph",
      "title_en": "Bal Gandharva",
      "content_en": "Bal Gandharva was one of the most famous...",
      "content_mr": null,
      "applies_from": 1,
      "applies_to": 2
    }
  ],
  "questions": [
    {
      "question_no": 1,
      "question_type": "context_text",
      "context_ref": 0,
      "text_en": "Choose the correct option to fill in the blank (A)",
      "text_mr": null,
      "correct_option": 2,
      "explanation_en": "'Bal Gandharva' was his stage name...",
      "difficulty": "easy",
      "options": [
        {"option_no": 1, "text_en": "School name"},
        {"option_no": 2, "text_en": "Stage name"},
        {"option_no": 3, "text_en": "Father's name"},
        {"option_no": 4, "text_en": "Village name"}
      ]
    }
  ]
}
```

---

## Review Trigger

Revisit if a new MSCE paper format introduces question types not covered
by the current enum (e.g. audio questions, drag-and-drop matching).
Revisit if question count per exam exceeds 150 and JOIN performance degrades.
