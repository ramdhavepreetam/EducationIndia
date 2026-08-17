# Content Integrity Audit — 2026-08-17

Audit of the ScholarPath question bank against MSCE paper-fidelity requirements.
Scope: live Supabase DB (16 exams / 1,200 questions / 4,800 options), the PDF
import pipeline, and the question delivery path.

---

## Executive summary

Structural conformance to the MSCE format is **excellent**. Content integrity is
**not** — the PDF import pipeline silently produced unanswerable questions across
most papers, and nothing in the system detected it.

| Area | Verdict |
|---|---|
| Paper structure (75Q / 150 marks / 90 min / 2 marks per Q) | PASS — all 16 exams |
| Section split 25/50 in correct papers | PASS — all 16 exams |
| Option integrity (exactly 4 options, exactly 1 correct) | PASS — all 1,200 questions |
| `correct_option` never exposed during delivery | PASS — view + schema + test |
| Question/option **content** present | **FAIL — see below** |
| Image questions actually carry an image | **FAIL — 396 of 398** |
| Mock assembler / blueprint weighting | FAIL — does not exist (out of scope) |

---

## Findings

### F1 — 375 questions have a blank correct answer (CRITICAL)

The correct option is an empty row: no `text_en`, no `text_mr`, no `image_url`.
The student cannot answer correctly no matter what they pick.

1,510 options overall are blank; 375 of them are the correct answer.

Worst-affected papers (whole papers destroyed):

| Exam | Year / Paper | Blank correct answers |
|---|---|---|
| 26 | 2017 P501 | 75 of 75 |
| 27 | 2017 P502 | 75 of 75 |
| 20 | 2020 P501 | 75 of 75 |
| 21 | 2020 P502 | 50 of 75 |
| 25 | 2018 P502 | 25 |
| 23 | 2019 P502 | 18 |

### F2 — 396 of 398 image-typed questions have no image

Questions typed `image_only` / `text_image` / `context_image` with
`question_image_url IS NULL` render as a blank box. Only exams 16 and 17 have
any images at all (19 total, on Cloudflare R2).

### F3 — A live paper was serving broken questions

Exam 16 (2022 P501) was `is_active = true` with Q38's correct answer blank.
Exam 17 (2022 P502) was `is_active = true` with 16 imageless questions and 13
blank correct answers — though it had **zero attempts**, so no student was
affected.

### F4 — Math notation is destroyed by text extraction

Exam 16 Q56 stem is stored as:

```
3 5 5
+ + = ?
4 6 8
```

That is the fraction sum 3/4 + 5/6 + 5/8 flattened into positional garbage by
the PDF text extractor. Its options are `'5'`, `''`, `'1'`, `'2\n24 18 18 24'` —
numerators and denominators scattered across option rows.

**Implication:** attaching images does not fix these. Any question whose content
is a fraction, a matrix, or a stacked expression is corrupted at the text layer.

### F5 — The whole-row crop strategy duplicates content (DESIGN ISSUE)

`extract_question_crops_from_pdf_bytes()` (pdf_importer.py:554) crops from one
question header to the next — capturing **the stem, the figure, AND all four
options** in a single PNG.

That crop is then stored in `question_image_url`, while the stem text and the
four options are *also* stored as text. The frontend
(`QuestionCard.jsx`, `WrongAnswerCard.jsx`) renders stem text → image → options
unconditionally, so the student sees:

- the question text
- an image that **contains the same question text and all four options**
- the four options again as clickable radio buttons

Verified on exam 16 Q1 (id 1143) and Q6 (id 1148): both have complete text and
complete options in the DB *and* a full-row crop. Q1 is not even an image
question — it is plain text with a redundant crop attached.

This is not merely cosmetic. It leaks the option layout as an unclickable image,
doubles visual load under a 1.2-minute-per-question time budget, and for
"select the correct image" items would show the answer figures in a form the
student cannot select.

**The crop should be clipped to the figure region only** — between the end of the
stem text and the start of option (1) — not the whole question block.

### F6 — `media_files` table does not exist

The media module defines a `MediaFile` model (`media/models.py`), but the table
is absent from the database. Question images are bare R2 URLs with no asset row,
so there is no `alt_text`, no dimensions, no provenance, and no way to find
orphaned or reused assets. `MediaService` writes would fail against this DB.

---

## Changes applied

### 1. Exam 17 unpublished
`UPDATE exams SET is_active=false WHERE id=17`
Zero attempts existed, so no data or student progress was affected.
**Rollback:** `UPDATE exams SET is_active=true WHERE id=17`

### 2. Exam 16 Q38 and Q56 cancelled
`is_cancelled = true` with a data-quality reason. The scorer already excludes
cancelled questions from the denominator (verified by
`test_scorer.py::test_cancelled_question_is_excluded_from_score_denominator`),
so exam 16 now scores out of **73 questions / 146 marks**.
`correct_option` was left intact as an audit trail.
**Rollback:** `UPDATE questions SET is_cancelled=false, cancelled_reason=NULL WHERE id IN (1180,1198)`

### 3. Integrity constraints + paper-health view
`database/migration_content_integrity_guards.sql`
Alembic revision `0008_content_integrity`.

Three `CHECK` constraints, added **`NOT VALID`**:

- `questions_stem_present_chk` — a question needs stem text or a stem image
- `questions_image_type_has_image_chk` — `image_only`/`text_image` needs an image
- `options_content_present_chk` — an option needs text or an image

`NOT VALID` is deliberate: with 1,510 existing violations a validating
constraint could not be added without first destroying or repairing real
content. These block **new** bad data immediately. Cancelled questions are
exempt (official answer keys legitimately withdraw items).

To validate once a paper's backlog is repaired (brief ACCESS EXCLUSIVE lock):
```sql
ALTER TABLE questions VALIDATE CONSTRAINT questions_stem_present_chk;
```

Plus `v_paper_health` — one row per exam with `publish_blocker_count`, the
count of questions that cannot be answered correctly. **Any paper with
`publish_blocker_count > 0` must not be published.**

Verified behaviour (all pass):

```
MUST REJECT:
  rejected :: question with no stem text and no image  [questions_stem_present_chk]
  rejected :: image_only question with NULL image_url  [questions_image_type_has_image_chk]
  rejected :: text_image question with NULL image_url  [questions_image_type_has_image_chk]
  rejected :: blank option (no text, no image)         [options_content_present_chk]
  rejected :: empty-string option                      [options_content_present_chk]
MUST ACCEPT:
  accepted :: normal text question
  accepted :: image_only WITH image
  accepted :: text option
  accepted :: image-only option (select-the-image)
  accepted :: marathi-only option
  accepted :: cancelled image_only with no image (exempt)
```

---

## Current paper health

Only exam 16 is published, and it is now clean:

| Exam | Year/Paper | Active | Missing images | Blank correct answers | Publish blockers |
|---|---|---|---|---|---|
| 16 | 2022 P501 | **yes** | 0 | 0 | **0** |
| 26 | 2017 P501 | no | 75 | 75 | 75 |
| 27 | 2017 P502 | no | 75 | 75 | 75 |
| 20 | 2020 P501 | no | 75 | 75 | 75 |
| 21 | 2020 P502 | no | 50 | 50 | 50 |
| 25 | 2018 P502 | no | 27 | 25 | 25 |
| 23 | 2019 P502 | no | 19 | 18 | 18 |
| 17 | 2022 P502 | no | 16 | 13 | 13 |
| 5 | 2024 P502 | no | 21 | 13 | 13 |
| 15 | 2023 P502 | no | 13 | 12 | 12 |
| 19 | 2021 P502 | no | 15 | 11 | 11 |
| 18 | 2021 P501 | no | 1 | 3 | 3 |
| 22 | 2019 P501 | no | 0 | 2 | 2 |
| 4 | 2024 P501 | no | 7 | 0 | 2 |
| 24 | 2018 P501 | no | 1 | 1 | 1 |
| 14 | 2023 P501 | no | 1 | 1 | 1 |

Query it any time: `SELECT * FROM v_paper_health ORDER BY publish_blocker_count DESC;`

---

### 4. Crop region fixed (F5)

`pdf_importer.py` — `extract_question_crops_from_pdf_bytes()` now clips to the
**figure band only**: from the bottom of the last stem line to the top of the
first option marker `(1)`. Helpers added:

- `_question_line_boxes()` — y-ordered text lines with bounding boxes
- `_figure_band()` — locates the band between stem and options; falls back to
  the whole block when no option marker is found (figure-only items whose
  options are themselves drawings)
- `_band_has_ink()` — pixel check that suppresses crops for questions with no
  figure, so plain text items no longer get a redundant image
- `_OPTION_LINE_RE` — matches `(1)`, `1)`, `[3]`, `4.` and Devanagari `(१)-(४)`

Verified on a synthetic fixture reproducing the real MSCE layout: before the
fix, a plain text question and a figure question both produced whole-block
crops containing the stem and all four options; after, the text question
produces **no crop** and the figure question produces a figure-only crop
(~200px tall vs the full block).

**Knock-on effect (intended):** the `has_*_crop_fallback` flags at
pdf_importer.py:407-453 key off `q_no in english_image_assets`. Fewer crops
means fewer questions silently suppress the
`"English extraction found N options"` error at line 440. Papers whose options
failed to extract will now surface that error at preview time instead of being
imported as a `text_image` question with a whole-block crop papering over it.
This is the behaviour that would have caught the 375 blank correct answers
during import. **Expect more preview errors on re-import — that is the fix
working, not a regression.**

Regression tests: `backend/app/modules/question/tests/test_pdf_crops.py`
(15 tests). Full backend suite: 236 passed.

### 5. Publish gate wired to v_paper_health

`catalog/service.py::publish_exam()` now refuses to activate a paper whose
`publish_blocker_count > 0` — questions with a blank correct answer or no stem,
which a student cannot answer correctly. This closes the loop: the constraints
stop bad *imports*, and this stops a broken paper reaching students through the
admin UI.

- `catalog/repository.py::get_paper_health()` reads the view (queries stay in
  the repository per CLAUDE.md)
- Raises `BadRequest` naming the count, the remedy (fix content or cancel the
  questions) and the diagnostic query
- `force=True` (`?force=true` on both routes) overrides deliberately; the
  response message then carries an explicit WARNING and the blocker count
- **Unpublish is never gated** — it is the remedy for a broken paper
- A paper with no health row (no questions yet) is not blocked

Routes: `PUT /api/admin/catalog/exams/{id}/publish` and
`PUT /api/catalog/exams/{id}/publish`.

Verified against the live database:

```
exam 17 (13 blockers) -> BLOCKED, is_active stayed false
exam 16 (0 blockers)  -> published OK
exam 17 with force    -> published, health reported 13 blockers back
```

Tests: `TestPublishHealthGate` (5 tests) in catalog/tests/test_service.py.
Full backend suite: 241 passed.

NOTE: the existing `mock_repo` fixture needed an explicit
`get_paper_health.return_value` — an auto-created AsyncMock returns a MagicMock
whose `.get()` is truthy, which would have read as "has blockers" and blocked
every publish test.

---

## Recommended next steps (not done)

1. **Re-import the salvageable papers** with the corrected crop logic, then
   validate the constraints per paper.
2. **Decide on 2017 and 2020** — 75/75 and 75/50 questions destroyed. These are
   likely manual re-entry, not re-import. Resourcing decision.
3. **Create the `media_files` table** (F6) or drop the unused model.
4. **Difficulty labelling** — 1,122 of 1,200 questions are `medium`. Blueprint-
   weighted mock assembly is impossible until this is real.
5. ~~Gate publishing on `v_paper_health`~~ — **DONE**, see change 5 above.

## Open assumptions

- `context_image` questions are exempt from the image constraint, since the
  image may legitimately live on the shared `question_contexts.image_url` row.
- Cancelled questions are exempt from all content constraints.
- Blank-option repair was **not** attempted; no content was invented or deleted.
