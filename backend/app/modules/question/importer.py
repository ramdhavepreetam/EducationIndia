"""
Question bulk importer — validation logic for ADR-004 question types.

validate_question_import() is called per-question before DB insertion.
Returns a list of error strings (empty list = valid).

Question type rules:
  text          → text_en required
  text_image    → text_en required, question_image_url required
  image_only    → text_en/mr must be None, image in question or context
  context_text  → context_ref required
  context_image → context_ref required
  marathi_only  → text_mr required, text_en must be None
  bilingual     → both text_en and text_mr required

All non-cancelled questions:
  - single-answer: correct_option must be 1-4
  - multi-select: correct_options must contain 1-4 values from option numbers

All types:
  - exactly 4 options required
  - image_only options: all 4 must have image_url
  - text/bilingual options: all 4 must have text_en
  - marathi_only options: all 4 must have text_mr
"""

from app.modules.question.schemas import QuestionImportItem


def validate_question_import(q: QuestionImportItem) -> list[str]:
    """
    Validate a single question import item.
    Returns list of error strings. Empty list means the question is valid.
    """
    errors: list[str] = []
    prefix = f"Q{q.question_no}"

    # ── Universal rules ───────────────────────────────────────────────────────

    if q.is_cancelled:
        if q.correct_option is not None or q.correct_options:
            errors.append(f"{prefix}: cancelled questions must not have correct answers")
    elif q.is_multi_select:
        if not q.correct_options:
            errors.append(f"{prefix}: multi-select questions require correct_options")
        else:
            invalid = [opt for opt in q.correct_options if opt not in (1, 2, 3, 4)]
            if invalid:
                errors.append(
                    f"{prefix}: correct_options values must be 1-4, got {invalid}"
                )
            if len(set(q.correct_options)) != len(q.correct_options):
                errors.append(f"{prefix}: correct_options must not contain duplicates")
    elif q.correct_option not in (1, 2, 3, 4):
        errors.append(f"{prefix}: correct_option must be 1-4, got {q.correct_option}")

    if len(q.options) != 4:
        errors.append(
            f"{prefix}: exactly 4 options required, got {len(q.options)}"
        )
        # Can't validate option content if count is wrong
        return errors

    option_nos = sorted(o.option_no for o in q.options)
    if option_nos != [1, 2, 3, 4]:
        errors.append(
            f"{prefix}: option_no values must be exactly [1,2,3,4], got {option_nos}"
        )

    # ── Type-specific question text rules ─────────────────────────────────────

    qtype = q.question_type

    if qtype == "text":
        if not q.text_en:
            errors.append(f"{prefix}: text type requires text_en")
        _validate_text_options(q, errors, prefix)

    elif qtype == "text_image":
        if not q.text_en and not q.text_mr:
            errors.append(f"{prefix}: text_image type requires text_en or text_mr")
        if not q.question_image_url:
            errors.append(f"{prefix}: text_image type requires question_image_url")
        _validate_language_text_options(q, errors, prefix)

    elif qtype == "image_only":
        if q.text_en is not None:
            errors.append(f"{prefix}: image_only type must not have text_en")
        if q.text_mr is not None:
            errors.append(f"{prefix}: image_only type must not have text_mr")
        # Must have image in question body or a context_ref
        if not q.question_image_url and q.context_ref is None:
            errors.append(
                f"{prefix}: image_only type requires question_image_url or context_ref"
            )
        _validate_image_options(q, errors, prefix)

    elif qtype == "context_text":
        if q.context_ref is None:
            errors.append(f"{prefix}: context_text type requires context_ref")
        if not q.text_en and not q.text_mr:
            errors.append(f"{prefix}: context_text type requires text_en or text_mr")
        _validate_text_options(q, errors, prefix)

    elif qtype == "context_image":
        if q.context_ref is None:
            errors.append(f"{prefix}: context_image type requires context_ref")
        _validate_image_options(q, errors, prefix)

    elif qtype == "marathi_only":
        if not q.text_mr:
            errors.append(f"{prefix}: marathi_only type requires text_mr")
        if q.text_en is not None:
            errors.append(f"{prefix}: marathi_only type must not have text_en")
        _validate_marathi_options(q, errors, prefix)

    elif qtype == "bilingual":
        if not q.text_en:
            errors.append(f"{prefix}: bilingual type requires text_en")
        if not q.text_mr:
            errors.append(f"{prefix}: bilingual type requires text_mr")
        # Bilingual options need either both or at least text_en
        _validate_text_options(q, errors, prefix)

    else:
        errors.append(
            f"{prefix}: unknown question_type '{qtype}'. Valid types: "
            "text, text_image, image_only, context_text, context_image, "
            "marathi_only, bilingual"
        )

    return errors


# ── Option validation helpers ─────────────────────────────────────────────────

def _validate_text_options(
    q: QuestionImportItem, errors: list[str], prefix: str
) -> None:
    """All 4 options must have text_en."""
    for opt in q.options:
        if not opt.text_en:
            errors.append(
                f"{prefix}: option {opt.option_no} requires text_en "
                f"(question type is '{q.question_type}')"
            )


def _validate_language_text_options(
    q: QuestionImportItem, errors: list[str], prefix: str
) -> None:
    """Validate option text for whichever language columns this question uses."""
    if q.text_en:
        _validate_text_options(q, errors, prefix)
    if q.text_mr and not q.text_en:
        _validate_marathi_options(q, errors, prefix)


def _validate_marathi_options(
    q: QuestionImportItem, errors: list[str], prefix: str
) -> None:
    """All 4 options must have text_mr (marathi_only question)."""
    for opt in q.options:
        if not opt.text_mr:
            errors.append(
                f"{prefix}: option {opt.option_no} requires text_mr "
                f"(question type is 'marathi_only')"
            )


def _validate_image_options(
    q: QuestionImportItem, errors: list[str], prefix: str
) -> None:
    """All 4 options must have image_url (image_only / context_image question)."""
    for opt in q.options:
        if not opt.image_url:
            errors.append(
                f"{prefix}: option {opt.option_no} requires image_url "
                f"(question type is '{q.question_type}')"
            )
