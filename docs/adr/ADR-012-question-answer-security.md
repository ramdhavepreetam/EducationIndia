# ADR-012: Question Answer Security

**Date:** 2025-02-21
**Status:** Accepted
**Decider:** Preetam
**Modules Affected:** question (owns), attempt (reads questions), analysis (reads answers)

---

## Context

The correct answer (correct_option) for each question must never be sent
to the frontend during an active exam. A student inspecting network requests
via browser dev tools must not be able to see the answer. This is not
theoretical — savvy students or parents can and do inspect API responses.
At the same time, the analysis module needs correct answers to score responses
after submission, and admins need to see and edit them. The security boundary
must be enforced at the data layer, not just the application layer.

---

## Decision

We will create two PostgreSQL views: v_exam_questions (excludes correct_option
and explanation — safe for exam delivery) and v_exam_answers (includes
correct_option and explanation — for post-exam review and admin only).
The QuestionService.get_questions_for_exam() method ALWAYS uses v_exam_questions.
The AnalysisService reads correct answers directly from questions table
server-side — never exposing them via an API endpoint during exam. RLS
restricts v_exam_answers to submitted attempts only.

---

## Alternatives Considered

### Option 1: Application-level filtering (remove field in serializer)
Pydantic schema for exam delivery excludes correct_option field.
- Pro: Simple to implement
- Con: Developer mistake in one endpoint exposes answers — no safety net
- Con: No database-level enforcement — depends entirely on application code

### Option 2: Separate answers table
questions table has no correct_option; answers table with (question_id, correct_option).
- Pro: Architecturally clean separation
- Con: Every scoring operation requires JOIN with answers table
- Con: Bulk import must insert to two tables per question
- Con: Admin question edit requires update on two tables

### Option 3: DB views with RLS ← CHOSEN
v_exam_questions (safe view) + v_exam_answers (restricted view)
- Pro: Enforced at PostgreSQL level — cannot be bypassed by application code
- Pro: questions table retains correct_option for simplicity
- Pro: Admin endpoints read from questions table directly (full access)
- Pro: Analysis service reads questions table server-side — never via API
- Con: Two views to maintain if questions table schema changes

---

## Consequences

### Positive
- Network inspection by student during exam shows zero correct answers
- Analysis module is the only server-side consumer of correct_option
- v_exam_answers available for result review — students see answers after submit
- RLS policy on attempts ensures student only sees answers for OWN submitted attempts

### Negative
- Developers must remember to use v_exam_questions in exam endpoints (documented in module README)
- v_exam_answers access tied to attempt status — complex RLS policy

### Neutral
- explanation_en + explanation_mr also excluded during exam delivery
  (no point showing explanation before student answers)
- hint_en + hint_mr available during PRACTICE mode (not timed mode)
  → practice mode flag on exam_assignments controls this

---

## Module Impact

```
database migration         → v_exam_questions view (no correct_option, no explanation)
database migration         → v_exam_answers view (full data including correct_option)
question/service.py        → get_questions_for_exam() queries v_exam_questions ONLY
question/repository.py     → get_for_exam_delivery() uses v_exam_questions view
analysis/service.py        → reads from questions table directly (server-side only, never via API)
question/router.py         → admin endpoints read from questions table (full access)
attempt/router.py          → POST /api/attempts/{id}/submit triggers analysis, returns score
                              (does NOT return correct answers at submission time)
analysis/router.py         → GET /api/analysis/attempts/{id}/report
                              (returns answers ONLY if attempt.status = 'submitted')
```

---

## Implementation Notes

View already in migration SQL — verify it excludes the right columns:
```sql
CREATE VIEW v_exam_questions AS
SELECT
    q.id, q.exam_id, q.section_id, q.topic_id, q.context_id,
    q.question_no, q.question_type,
    q.text_en, q.text_mr,
    q.question_image_url, q.question_image_alt_en, q.question_image_alt_mr,
    q.marks, q.difficulty, q.tags,
    -- correct_option     ← INTENTIONALLY EXCLUDED
    -- explanation_en     ← INTENTIONALLY EXCLUDED
    -- explanation_mr     ← INTENTIONALLY EXCLUDED
    -- hint_en, hint_mr   ← Excluded during exam; included for practice mode separately
    s.subject_en, s.subject_mr, s.section_label,
    t.name_en AS topic_name_en, t.name_mr AS topic_name_mr,
    qc.context_type, qc.content_en, qc.content_mr, qc.title_en, qc.title_mr,
    qc.image_url AS context_image_url, qc.instruction_en, qc.instruction_mr
FROM questions q
LEFT JOIN sections s ON s.id = q.section_id
LEFT JOIN topics t ON t.id = q.topic_id
LEFT JOIN question_contexts qc ON qc.id = q.context_id;
```

Analysis service correct answer access (server-side only):
```python
# analysis/service.py — reads directly from questions table
# This runs SERVER-SIDE after submission, result stored in attempts.JSONB
async def generate_report(attempt_id: str, db: AsyncSession) -> ReportData:
    # Load raw responses
    responses = await db.execute(
        select(Response).where(Response.attempt_id == attempt_id)
    )
    # Load correct answers SERVER-SIDE
    question_ids = [r.question_id for r in responses]
    questions = await db.execute(
        select(Question.id, Question.correct_option, Question.topic_id)
        .where(Question.id.in_(question_ids))
    )
    # Pass to pure scorer — no DB access in scorer
    return scorer.calculate_score(responses, questions)
```

Practice mode hint exposure (allowed):
```python
# Only when assignment_type == 'practice'
if assignment.assignment_type == "practice":
    # Return hints but still NOT correct_option
    # Student sees hint only after attempting the question
    return QuestionWithHintResponse(...)
```

---

## Review Trigger

Revisit if exam anti-cheat requirements increase (e.g. randomised question
order per student, randomised option order). Those features require changes
to exam delivery but not to this security model. Revisit if practice mode
needs "show answer after each question" — that requires post-answer correct
option exposure, which is acceptable only for practice mode assignments.
