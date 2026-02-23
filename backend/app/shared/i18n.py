"""
i18n utilities for ScholarPath.

Multilingual design rule (from CLAUDE.md):
  All user-facing text columns follow the pattern: column_en, column_mr
  To add Hindi later: ALTER TABLE ... ADD COLUMN column_hi TEXT
  Nothing else changes.

Usage:
    lang = get_language(request)
    title = pick(exam, "title", lang)   # returns exam.title_mr or exam.title_en
"""

from typing import Any, Optional

from fastapi import Request

SUPPORTED_LANGUAGES: frozenset[str] = frozenset({"en", "mr", "hi"})
DEFAULT_LANGUAGE: str = "en"

# Request header that frontend sends (e.g. X-Language: mr)
LANGUAGE_HEADER: str = "X-Language"


def get_language(request: Request) -> str:
    """
    Resolve the preferred language for a request.

    Priority order:
      1. X-Language header  (set by frontend based on user's profile preference)
      2. lang query param   (?lang=mr — useful for direct URL sharing)
      3. Accept-Language header  (browser default)
      4. "en" fallback
    """
    # 1. Custom header
    lang = request.headers.get(LANGUAGE_HEADER, "").lower().strip()
    if lang in SUPPORTED_LANGUAGES:
        return lang

    # 2. Query param
    lang = request.query_params.get("lang", "").lower().strip()
    if lang in SUPPORTED_LANGUAGES:
        return lang

    # 3. Accept-Language (parse first tag only, ignore quality values)
    accept = request.headers.get("Accept-Language", "")
    for tag in accept.split(","):
        code = tag.strip().split(";")[0].strip()[:2].lower()
        if code in SUPPORTED_LANGUAGES:
            return code

    return DEFAULT_LANGUAGE


def pick(obj: Any, field: str, lang: str) -> Optional[str]:
    """
    Return the value of `{field}_{lang}` from obj, falling back to `{field}_en`.

    Works on SQLAlchemy model instances and plain dicts.

    Examples:
        pick(exam, "title", "mr")   # returns exam.title_mr ?? exam.title_en
        pick(data, "name", "hi")    # returns data["name_hi"] ?? data["name_en"]
    """
    if isinstance(obj, dict):
        return obj.get(f"{field}_{lang}") or obj.get(f"{field}_en")
    return getattr(obj, f"{field}_{lang}", None) or getattr(obj, f"{field}_en", None)


def pick_fields(obj: Any, fields: list[str], lang: str) -> dict[str, Optional[str]]:
    """
    Convenience wrapper — pick multiple fields at once.

    Example:
        pick_fields(exam, ["title", "instructions"], "mr")
        # → {"title": "...", "instructions": "..."}
    """
    return {field: pick(obj, field, lang) for field in fields}
