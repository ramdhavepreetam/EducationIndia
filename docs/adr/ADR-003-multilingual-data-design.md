# ADR-003: Multilingual Data Design

**Date:** 2025-02-21
**Status:** Accepted
**Decider:** Preetam
**Modules Affected:** question, catalog, analysis, user (all content-serving modules)

---

## Context

ScholarPath serves two distinct languages from day one: English and Marathi.
The actual MSCE exam papers confirm the complexity — some questions exist in
both languages (bilingual), some only in Marathi (Marathi section Q1-25 in
Paper 0502), and some have no translatable text at all (image_only Intelligence
Test questions). In the future, Hindi and potentially other Indian languages
may be added. The multilingual approach must be simple to implement now and
cheap to extend later without breaking existing API contracts.

---

## Decision

We will use parallel language columns on each table (_en, _mr suffix pattern).
Every user-facing text field gets a pair: title_en + title_mr, text_en + text_mr,
explanation_en + explanation_mr. Either column can be NULL when that language
version doesn't exist. A shared utility function get_text(obj, lang) resolves
which column to read and falls back to English if the requested language is null.
To add Hindi: ALTER TABLE questions ADD COLUMN text_hi TEXT — nothing else changes.

---

## Alternatives Considered

### Option 1: Separate translation table (i18n style)
One content table, one translations table with (content_id, language, field, value).
- Pro: Theoretically clean, add any language by inserting rows
- Con: Every question fetch requires joins across 3+ tables
- Con: Complex queries for "give me all questions in Marathi with English fallback"
- Con: Much harder for admin bulk import (CSV/JSON becomes complex)
- Con: AI-generated queries become error-prone with deeply joined schemas

### Option 2: JSONB language map column
Single column: content JSONB = {"en": "...", "mr": "...", "hi": "..."}
- Pro: Single column, easy to add languages
- Con: Loses PostgreSQL type safety and indexing on individual languages
- Con: Full-text search on Marathi text becomes complicated
- Con: ORM mapping is awkward (SQLAlchemy doesn't map JSONB sub-fields cleanly)

### Option 3: Parallel language columns ← CHOSEN
text_en TEXT, text_mr TEXT (add text_hi later via ALTER TABLE)
- Pro: Simple SQL, clean ORM models, straightforward API responses
- Pro: Full-text search index per language (separate GIN indexes)
- Pro: NULL means "not available in this language" — explicit and queryable
- Pro: ALTER TABLE to add new language — zero API contract change
- Con: Column count grows with each language (acceptable trade-off)
- Con: Partial denormalization if content is identical across languages

---

## Consequences

### Positive
- Admin bulk import JSON is readable: {"text_en": "...", "text_mr": "..."}
- API response is clean: question.text_en and question.text_mr always present
- Frontend language switch is instant — all translations already in response
- New language support: ALTER TABLE + populate columns + add to get_text()

### Negative
- If same content in 3+ languages, same data stored multiple times
- Each new language adds 5-10 columns across multiple tables
- Schema migration required per language addition (acceptable — rare event)

### Neutral
- NULL column = "not available in this language" → frontend shows English fallback
- Admin UI must show both language fields for all content entry forms
- Marathi-only questions (Paper 0502 Section I) have text_en = NULL by design

---

## Module Impact

```
question/models.py     → text_en, text_mr, explanation_en, explanation_mr,
                          hint_en, hint_mr (all paired)
question_contexts      → content_en, content_mr, title_en, title_mr,
                          instruction_en, instruction_mr
options                → text_en, text_mr
catalog/models.py      → All name/title/description fields paired
sections               → subject_en, subject_mr
topics                 → name_en, name_mr
exam_events            → title_en, title_mr
exams                  → title_en, title_mr, instructions_en, instructions_mr
user_profiles          → preferred_language column (drives default)
shared/i18n.py         → get_text() utility function (shared across all modules)
notifications          → title_en, title_mr, body_en, body_mr
```

---

## Implementation Notes

Shared utility (shared/i18n.py):
```python
def get_text(obj: Any, lang: str, field: str) -> Optional[str]:
    """
    Get text in requested language with English fallback.
    
    Usage:
        get_text(question, "mr", "text")
        # Returns question.text_mr if not None, else question.text_en
    """
    primary = getattr(obj, f"{field}_{lang}", None)
    if primary:
        return primary
    # Fallback to English
    return getattr(obj, f"{field}_en", None)
```

API response pattern — always return both languages:
```python
class QuestionResponse(BaseModel):
    id: int
    text_en: Optional[str]
    text_mr: Optional[str]
    # Frontend decides which to display based on user preference
    # No server-side language filtering — send both, client chooses
```

Frontend translation file structure:
```
/src/shared/i18n/
  en/translation.json   → UI strings (buttons, labels, messages) in English
  mr/translation.json   → UI strings in Marathi
  # Question text comes from DB, not from these files
```

---

## Review Trigger

Revisit when adding Hindi language support — follow ALTER TABLE pattern.
Revisit if question content volume exceeds 10,000 rows and storage cost
of duplicate language columns becomes meaningful.
