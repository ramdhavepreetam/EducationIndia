# Mock Test 2026 — Paper I

Vendor-produced practice paper, imported as a scratch exam for end-to-end testing
of the JSON import path (see `docs/vendor/QUESTION_PAPER_SPEC.md`).

## Contents

| File | Purpose |
|---|---|
| `MSCE_Class5_Paper1_Mock_Test_2026.json` | the delivered paper, as received |
| `import_mock_paper.py` | creates the exam event/exam/sections/topics and inserts all 75 questions |
| `generate_figures.py` | draws the geometry, mirror-image and dice figures (Pillow) |
| `generate_q8_illustration.py` | draws the Q8 garden scene (Pillow) |

Images are written to `uploads/mock2026/` and served at `/static/mock2026/…`.
Both generator scripts are deterministic — re-running reproduces byte-identical PNGs.

## Paper summary

```
75 questions · 4 contexts · 150 marks · 90 minutes
bilingual 46 · text 17 · context_text 8 · text_image 3 · image_only 1
9 multi-select "choose two" questions
publish_blocker_count: 0
```

## Regenerating

```bash
.venv/bin/python backend/scripts/mock2026/generate_figures.py
.venv/bin/python backend/scripts/mock2026/generate_q8_illustration.py
```

## Re-importing

`import_mock_paper.py` creates a NEW exam event and exam on every run — it does
not update in place. Delete the previous scratch exam first if you re-run it,
or you will accumulate duplicates.

After import, run this once: the `sync_correct_option` trigger fires on UPDATE,
not INSERT, so `options.is_correct` is not populated by a fresh insert. Scoring
reads `questions.correct_option` and is unaffected, but `v_exam_answers` and the
post-exam review read `options.is_correct`.

```sql
UPDATE questions SET correct_option = correct_option
  WHERE exam_id = :exam_id AND correct_option IS NOT NULL;

UPDATE options o SET is_correct = true FROM questions q
  WHERE q.id = o.question_id AND q.exam_id = :exam_id
    AND q.is_multi_select AND o.option_no = ANY(q.correct_options);
```

## Known limitation

The Q8 illustration is programmatic flat-vector art. It is clear and readable,
but simpler than typical MSCE exam artwork. To replace it with commissioned art,
drop a new file at `uploads/mock2026/q8-picture.png` — no database change needed.
