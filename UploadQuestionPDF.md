# Uploading Question PDFs With Image Questions

This document explains the strategy used to import MSCE question papers from PDF, handle visual/image-based questions, upload images, and store the final data in Supabase.

## Goal

The question bank is the core of ScholarPath. The import process must prioritize correctness over speed:

- Extract text questions and options from the PDF where the PDF text layer is reliable.
- Detect questions whose content/options are visual figures.
- Render those visual questions as image crops.
- Upload image crops to Cloudflare R2.
- Store public image URLs in Supabase.
- Keep the import review-first so bad extraction does not silently overwrite exam data.

## Main Strategy

We use a hybrid import strategy:

1. Parse question text and options from the PDF text layer.
2. Parse the official answer key from the answer sheet.
3. Build a preview manifest before writing anything.
4. If a question has visual/vector content that cannot be extracted as text, render a crop from the PDF page.
5. Upload the crop to R2.
6. Save the R2 public URL in `questions.question_image_url`.
7. Use simple option labels such as `Option 1`, `Option 2`, `Option 3`, `Option 4` when the option choices are visible inside the question image.

Example: 2022 Std 5 Paper 501 Q47 had vector figure options. The PDF text layer only contained option labels, not the actual figures. We rendered the full Q47 block as a PNG and stored it as a `text_image` question.

## Relevant Code

- PDF importer: `backend/app/modules/question/pdf_importer.py`
- Import service: `backend/app/modules/question/service.py`
- Admin endpoint: `POST /api/admin/questions/pdf-import`
- Admin UI: `frontend/src/modules/admin/components/PdfExamImporter.jsx`
- R2 provider: `backend/app/modules/media/providers/r2.py`
- Question display: `frontend/src/modules/attempt/components/QuestionCard.jsx`

## Data Model

For normal text questions:

- `questions.question_type = 'text'`
- `questions.text_en` or `questions.text_mr` contains the question stem.
- `questions.question_image_url = NULL`
- `options.text_en` or `options.text_mr` contains each option.

For image-backed questions:

- `questions.question_type = 'text_image'` when there is text plus a figure.
- `questions.question_type = 'image_only'` only when the image is the whole question and no useful stem exists.
- `questions.text_en` should still contain the short instruction where available.
- `questions.question_image_url` stores the public R2 URL.
- `questions.question_image_alt_en` stores a useful alt label.
- Options can either be:
  - real text in `options.text_en`, or
  - simple labels like `Option 1` to `Option 4` when the visual choices are already in the question image.

For cancelled official-key questions:

- `questions.is_cancelled = true`
- `questions.cancelled_reason = 'Cancelled in official answer key'`
- `questions.correct_option = NULL`
- Scoring excludes cancelled questions from the denominator.

## Image Upload Path

Images are uploaded to Cloudflare R2 using this folder structure:

```text
exams/{exam_id}/questions/{question_id}/{uuid}.png
```

Example:

```text
exams/16/questions/1189/c23635d4d2064b0bb8a232c01bc991be.png
```

The public URL is then stored directly in:

```sql
questions.question_image_url
```

Important: in the current production database, `media_files` may not exist. If it does not exist, do not depend on inserting a media record. Upload to R2 and update the question/option URL column directly.

## Review-First Workflow

Always use preview before apply.

Preview should confirm:

- 75 questions extracted for the paper.
- Answer key count matches the official key.
- Cancelled questions are detected and marked as cancelled, not treated as missing answers.
- Ambiguous questions are listed as errors.
- Image crops are non-blank and include the full figure/options.
- No question contains leaked next-question text or instruction blocks.

Only apply after preview has:

```text
errors: []
importable_count: 75
```

## Handling Image Questions

Some MSCE PDFs contain diagrams as vector drawing operations, not embedded images and not text. In those cases, `page.get_text()` can show:

```text
(1)
(2)
(3)
(4)
```

but the actual option figures are missing.

Strategy:

1. Detect that the question has fewer than four extracted option texts.
2. Check whether a PDF crop is available for that question number.
3. Render the full question block from the question header to the next question header.
4. Store the rendered PNG as a question image.
5. Set `question_type = 'text_image'`.
6. Set `text_en` to the short stem.
7. Set options to `Option 1` through `Option 4`.

This preserves the visual choices exactly as they appear in the paper.

## Crop Quality Rules

A good crop must:

- Start at the question number/stem.
- Include all figures and all four visual options.
- Stop before the next question.
- Avoid rough-work/footer/header text.
- Render large enough for student UI inspection.
- Return a public URL that loads with HTTP `200`.

For PyMuPDF rendering, the current approach uses:

```python
page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=rect, alpha=False)
```

The `2x` matrix gives readable PNG output without making files too large.

## R2 Requirements

Backend environment must include:

```bash
MEDIA_PROVIDER=r2
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=...
R2_PUBLIC_URL=...
```

Do not commit these values.

The deployed backend also needs these Python dependencies:

```text
PyMuPDF
numpy
opencv-python-headless
aioboto3
```

These are in `backend/requirements.txt`.

## Supabase Updates

For an image question, update:

```sql
UPDATE questions
SET question_type = 'text_image',
    text_en = :stem,
    question_image_url = :public_url,
    question_image_alt_en = :alt_text
WHERE exam_id = :exam_id
AND question_no = :question_no;
```

For image-visible options:

```sql
UPDATE options
SET text_en = :label,
    image_url = NULL
WHERE question_id = :question_id
AND option_no = :option_no;
```

For a text extraction cleanup:

```sql
UPDATE questions
SET question_type = 'text',
    text_en = :clean_question_text,
    question_image_url = NULL
WHERE exam_id = :exam_id
AND question_no = :question_no;
```

Then update each option text cleanly.

## Common Problems And Fixes

### Problem: option text includes the next instruction block

Example:

```text
Exclamatory mark.
Instruction for Question No. 14 and 15...
```

Fix:

- Strip instruction blocks during extraction.
- Patch the affected live option text.
- Add extraction tests or preview checks for instruction leakage.

### Problem: image question shows empty options

Cause:

- The visual choices are vector drawings in the PDF.
- The PDF text layer does not contain those shapes.

Fix:

- Crop the full question block.
- Upload the crop to R2.
- Set `question_type = 'text_image'`.
- Set options to `Option 1` to `Option 4`.

### Problem: image uploaded but DB update failed

Cause:

- R2 upload succeeded, but DB transaction rolled back.
- This can happen if optional `media_files` table is missing.

Fix:

- Reuse the uploaded R2 public URL.
- Patch `questions.question_image_url` directly.
- Verify with `curl -I <url>` and a DB query.

### Problem: cancelled question has no correct answer

Do not invent an answer. Mark it cancelled:

```sql
UPDATE questions
SET is_cancelled = true,
    cancelled_reason = 'Cancelled in official answer key',
    correct_option = NULL,
    correct_options = NULL
WHERE exam_id = :exam_id
AND question_no = :question_no;
```

## Verification Checklist

Before applying:

- Preview returns 75 questions.
- Preview returns no blocking errors.
- Answer key count and cancelled questions match the official sheet.
- All image crops are reviewed.

After applying:

- Query DB for image-backed questions:

```sql
SELECT question_no, question_type, text_en, question_image_url
FROM questions
WHERE exam_id = :exam_id
ORDER BY question_no;
```

- Verify options:

```sql
SELECT q.question_no, o.option_no, o.text_en, o.image_url, o.is_correct
FROM questions q
JOIN options o ON o.question_id = q.id
WHERE q.exam_id = :exam_id
ORDER BY q.question_no, o.option_no;
```

- Check each R2 URL:

```bash
curl -I "https://..."
```

- Call the delivery endpoint:

```bash
curl "https://<backend>/api/questions/?exam_id=<exam_id>"
```

- Open the student exam UI and inspect:
  - text questions
  - image questions
  - section navigation
  - option selection
  - save/resume

## Example: 2022 Std 5 Paper 501 Q47

Q47 was “Complete the following series.”

Issue:

- The text layer had the stem and option numbers.
- The actual arrows/stars figures were vector drawings.
- Options were empty in Supabase.

Fix:

- Rendered the full Q47 question block as PNG.
- Uploaded PNG to R2.
- Updated:
  - `questions.question_type = 'text_image'`
  - `questions.text_en = 'Complete the following series.'`
  - `questions.question_image_url = <R2 public URL>`
  - `options.text_en = 'Option 1' ... 'Option 4'`
  - `questions.correct_option = 1`

Result:

- Student UI shows the full figure and four visual choices.
- Option buttons select `Option 1` to `Option 4`.
- Scoring uses the official key.

## Recommended Future Strategy

For every new exam:

1. Import one paper at a time.
2. Keep the exam unpublished while importing.
3. Run preview.
4. Review all warnings and image crop candidates.
5. Apply only when preview is clean.
6. Manually spot-check at least:
   - first 5 questions
   - every context/instruction group
   - every image/figure question
   - last 5 questions
7. Publish only after student UI verification.

Avoid bulk-applying multiple papers until the first paper is fully verified end to end.
