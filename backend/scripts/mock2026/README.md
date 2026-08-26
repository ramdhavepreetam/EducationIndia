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

## Image URLs must be absolute

The vendor JSON carries bare filenames. They are stored as absolute URLs
(`http://localhost:8000/static/mock2026/…`) because the frontend dev server runs
on a different origin (:5173) than the backend (:8000). A relative
`/static/…` path resolves against the frontend, which returns `index.html`
instead of the PNG — the browser then shows a broken-image icon with alt text.

`import_mock_paper.py` handles this via `img()`. Override the host with:

```bash
BASE_URL=https://your-backend.example.com .venv/bin/python \
  backend/scripts/mock2026/import_mock_paper.py
```

To repoint images after the backend moves:

```sql
UPDATE questions SET question_image_url =
  replace(question_image_url, 'http://localhost:8000', 'https://NEW-HOST')
  WHERE exam_id = :exam_id AND question_image_url LIKE 'http://localhost:8000%';

UPDATE options o SET image_url =
  replace(o.image_url, 'http://localhost:8000', 'https://NEW-HOST')
  FROM questions q WHERE q.id = o.question_id AND q.exam_id = :exam_id
    AND o.image_url LIKE 'http://localhost:8000%';
```

## Known limitation

The Q8 illustration is programmatic flat-vector art. It is clear and readable,
but simpler than typical MSCE exam artwork. To replace it with commissioned art,
drop a new file at `uploads/mock2026/q8-picture.png` — no database change needed.
