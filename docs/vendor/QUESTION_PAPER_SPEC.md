# ScholarPath — Question Paper JSON Specification

**For content vendors producing MSCE scholarship exam papers.**

Deliver one JSON file per paper. This document is the complete spec — you do not
need database access or any ScholarPath code to produce a valid file.

Version 1.0 · 2026-08-17

---

## 1. Paper structure

Every MSCE paper is fixed:

| | Paper I | Paper II |
|---|---|---|
| Section I | First Language (English) — Q1–25 | Third Language (Marathi) — Q1–25 |
| Section II | Mathematics — Q26–75 | Intelligence Test — Q26–75 |
| Total | 75 questions, 150 marks | 75 questions, 150 marks |
| Duration | 90 minutes | 90 minutes |

Every question: **exactly 4 options, exactly 1 correct answer, 2 marks, no negative marking.**

---

## 2. File shape

```json
{
  "paper": {
    "board": "MSCE",
    "std_class": 5,
    "year": 2025,
    "paper_code": "501",
    "set_code": "A",
    "medium": "english"
  },
  "contexts": [ ... ],
  "questions": [ ... ]
}
```

- `paper_code` — `"501"` = Paper I, `"502"` = Paper II
- `std_class` — `4`, `5`, `7` or `8`
- `medium` — `"english"` or `"marathi"`
- `contexts` — shared passages/figures used by more than one question. Empty array `[]` if none.
- `questions` — all 75, in order.

---

## 3. Question object — every field

```json
{
  "question_no": 1,
  "section": "English",
  "topic": "Vocabulary",
  "question_type": "text",
  "text_en": "Which of the following letters make a meaningful word?",
  "text_mr": "खालीलपैकी कोणती अक्षरे अर्थपूर्ण शब्द बनवतात?",
  "question_image": null,
  "question_image_alt_en": null,
  "question_image_alt_mr": null,
  "correct_option": 3,
  "explanation_en": "'Exercise' is the only correctly spelled word.",
  "explanation_mr": "'Exercise' हा एकमेव योग्य शब्द आहे.",
  "hint_en": "Say each option aloud.",
  "hint_mr": "प्रत्येक पर्याय मोठ्याने वाचा.",
  "difficulty": "easy",
  "tags": ["spelling", "vocabulary"],
  "context_ref": null,
  "options": [
    { "option_no": 1, "text_en": "Excercise", "text_mr": "Excercise", "image": null },
    { "option_no": 2, "text_en": "Excersize", "text_mr": "Excersize", "image": null },
    { "option_no": 3, "text_en": "Exercise",  "text_mr": "Exercise",  "image": null },
    { "option_no": 4, "text_en": "Exersize",  "text_mr": "Exersize",  "image": null }
  ]
}
```

### Field reference

| Field | Required | Notes |
|---|---|---|
| `question_no` | yes | 1–75, unique, must fall in the section's range |
| `section` | yes | `"English"`, `"Mathematics"`, `"Marathi"`, `"Intelligence Test"` |
| `topic` | yes | see §7 for the allowed list per section |
| `question_type` | yes | see §4 |
| `text_en` / `text_mr` | depends on type | the question stem |
| `question_image` | depends on type | filename only, e.g. `"q29-stem.png"` — see §6 |
| `question_image_alt_en` / `_mr` | if image present | describe the figure in words |
| `correct_option` | yes | `1`–`4`. **Null only if `is_cancelled` is true** |
| `explanation_en` / `_mr` | recommended | shown after the exam |
| `hint_en` / `hint_mr` | optional | practice mode only |
| `difficulty` | yes | `"easy"`, `"medium"`, `"hard"` |
| `tags` | optional | free-text array |
| `context_ref` | if type needs it | 0-based index into `contexts` |
| `options` | yes | **exactly 4**, `option_no` 1,2,3,4 |

### Difficulty mix per paper

Aim for **40% easy / 40% medium / 20% hard** in each section.
Paper of 75: roughly 30 easy, 30 medium, 15 hard.

> Do **not** mark everything `"medium"`. An unlabelled bank makes
> blueprint-weighted practice papers impossible to generate.

---

## 4. The 7 question types

| Type | Stem | Options | Use for |
|---|---|---|---|
| `text` | text | text | most questions |
| `text_image` | text + image | text | geometry, charts, pictographs |
| `image_only` | image only | **images** | "select the correct figure" |
| `context_text` | text + shared passage | text | reading comprehension |
| `context_image` | shared figure | **images** | figure series sharing one diagram |
| `marathi_only` | Marathi only | Marathi | Paper II Section I |
| `bilingual` | both languages | both | shown side by side |

### Rules per type — these are enforced, a file that breaks them is rejected

**`text`** — `text_en` required. All 4 options need `text_en`.

**`text_image`** — stem text required **and** `question_image` required.
> The image must show **only the figure**. Never include the question text or
> the options inside the image — the app renders those separately, and a student
> would see them twice.

**`image_only`** — `text_en` and `text_mr` must both be `null`.
`question_image` required. **All 4 options must have `image`.**
Put the wording in `question_image_alt_en` / `_mr`.

**`context_text`** — `context_ref` required. Stem text required. Text options.

**`context_image`** — `context_ref` required. **All 4 options must have `image`.**

**`marathi_only`** — `text_mr` required, `text_en` must be `null`.
All 4 options need `text_mr`.

**`bilingual`** — both `text_en` and `text_mr` required. Supply both languages on options.

---

## 5. Symbols instead of images — please use these where possible

Unicode symbols render natively in the app. They need **no image file**, cannot
break, scale to any screen, and work across every language edition. Multi-line
layouts are preserved.

**Use symbols for:** series, patterns, odd-one-out, mirror/water image,
rotation, simple shape classification, fractions, powers, roots, angles.

```
circles    ○ ● ◐ ◑ ◒ ◓ ◔ ◕ ⬤ ◎
squares    □ ■ ◧ ◨ ◩ ◪ ▣ ⬛ ⬜
triangles  △ ▲ ▽ ▼ ◁ ◀ ▷ ▶
other      ◇ ◆ ◈ ☆ ★ ✓ ✗
arrows     ↑ ↓ ← → ↖ ↗ ↘ ↙ ⇒ ↔ ⟲ ⟳
maths      ½ ¾ ⅓ ⅔ ¼ x² x³ √ ∠ ° ± × ÷ ≠ ≤ ≥ ⊂ ⊃ ∪ ∩ ∈ π
```

Multi-line grids work — use real newlines and align with spaces:

```json
"text_en": "Find the missing figure.\n\n△  ▽  △\n▽  △  ▽\n△  ▽  ?"
```

**Use IMAGES, not symbols, for:**

- **dice** — MSCE dice questions show a 3D cube with 2–3 visible faces.
  The `⚀⚁⚂` glyphs are flat single faces and also render as colour emoji,
  which look different on every device. Always supply a dice image.
- **clock faces** — same emoji problem. Use an image.
- paper folding, embedded/hidden figures
- geometry with labelled vertices or shaded regions
- coordinate grids, pictographs
- anything where perspective or exact proportion carries the answer

---

## 6. Images

- Reference **filenames only** in the JSON: `"q29-opt1.png"`. Not full URLs.
- Deliver all images in one flat folder alongside the JSON.
- **PNG** (transparent or white background) or **SVG**. SVG preferred for
  line figures — smaller and sharp at any size.
- Minimum 300px on the long edge. Crop tight to the figure, no page margins.
- Black on white. No colour dependence — some students print papers.
- Name predictably: `q<NN>-stem.png`, `q<NN>-opt1.png` … `q<NN>-opt4.png`,
  `ctx<N>-figure.png`.
- **Every image needs alt text** in `question_image_alt_en` / `_mr` (or
  `image_alt_en` / `_mr` on options). Describe what the figure shows — this is
  used for accessibility and for content review.

---

## 7. Allowed `topic` values

Use the exact strings below. If a question does not fit any topic, use the
closest and flag it in your delivery notes.

**English** (Paper I, Q1–25)
`Reading Comprehension` · `Poetry` · `Advertisement Reading` · `Grammar` ·
`Vocabulary` · `Picture Comprehension`

**Mathematics** (Paper I, Q26–75)
`Weights and Measures` · `Fractions` · `Profit and Loss` · `Simple Interest` ·
`Geometry` · `Percentages` · `Time and Distance` · `Number System` ·
`Data Handling` · `Algebra` · `Calendar and Clock`

**Marathi** (Paper II, Q1–25)
`Vocabulary` · `Grammar` · `Reading Comprehension` · `Poetry` ·
`Idioms and Proverbs`

**Intelligence Test** (Paper II, Q26–75)
`Mirror and Water Images` · `Analogy` · `Series Completion` ·
`Pattern Recognition` · `Direction and Position` · `Coding and Decoding` ·
`Venn Diagrams` · `Number Puzzles` · `Odd One Out` · `Logic and Reasoning`

---

## 8. Contexts (shared passages and figures)

When several questions share one passage or one diagram, put it in `contexts`
and point at it with `context_ref` (0-based index).

```json
"contexts": [
  {
    "context_type": "paragraph",
    "title_en": "The Clever Crow",
    "content_en": "A thirsty crow found a pitcher ...",
    "content_mr": "एका तहानलेल्या कावळ्याला ...",
    "image": null,
    "instruction_en": "Read the passage and answer questions 3 to 5.",
    "instruction_mr": "उतारा वाचून प्रश्न ३ ते ५ ची उत्तरे द्या.",
    "applies_from": 3,
    "applies_to": 5
  }
]
```

`context_type` must be one of:
`paragraph` · `poem` · `advertisement` · `image` · `pictograph` ·
`instruction` · `venn_diagram` · `figure_series` · `table` · `data_chart`

---

## 9. Cancelled questions

If the official answer key withdraws a question:

```json
"is_cancelled": true,
"cancelled_reason": "Cancelled in official answer key — two options correct",
"correct_option": null
```

`correct_option` **must** be `null`. Options still need content.

---

## 10. Delivery checklist

Before sending a paper, confirm:

- [ ] Exactly 75 questions, numbered 1–75 with no gaps or duplicates
- [ ] Q1–25 use the Section I topic list; Q26–75 use Section II
- [ ] Every question has exactly 4 options numbered 1,2,3,4
- [ ] Every `correct_option` is 1–4 (or null **only** if cancelled)
- [ ] **No option is blank** — every option has text or an image
- [ ] `image_only` / `context_image` questions: all 4 options have images
- [ ] Every referenced image file is in the delivery folder
- [ ] Every image has alt text
- [ ] Difficulty is spread ~40/40/20, not all "medium"
- [ ] JSON is valid UTF-8 and parses
- [ ] Marathi text is real Unicode Devanagari — **not** a legacy font
      encoding such as Shree Dev or Kruti Dev

> The single most common defect we have seen is a **blank correct answer** —
> the right option imported as an empty string. The student then cannot answer
> the question correctly no matter what they choose. Please check this
> explicitly.

---

## 11. Worked example and self-check

`question-paper-example.json` — a valid file demonstrating the question types,
symbol figures, a shared context, a multi-line grid, a dice question using an
image, and a cancelled question.

`check_paper.py` — run this against your file **before delivering**. Pure
Python 3, no dependencies, no database access:

```
python3 check_paper.py mypaper.json
python3 check_paper.py mypaper.json --images ./images   # verify image files exist
python3 check_paper.py mypaper.json --strict            # require all 75 questions
```

Exit code 0 means the paper is accepted. Errors must be fixed. Warnings are
advisory — review them, but they do not block delivery.

> One warning is a known false positive: a Marathi field containing only Latin
> characters is flagged as possible legacy-font encoding. For a genuinely
> English answer (a spelling question, a proper noun, a numeral) this is
> expected and can be ignored.
