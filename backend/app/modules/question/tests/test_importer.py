"""
Question importer unit tests — validates all 7 question types.

Tests validate_question_import() pure function.
No DB or async required — pure function tests.
Run: pytest backend/app/modules/question/tests/test_importer.py -v
"""

import pytest
from app.modules.question.importer import validate_question_import
from app.modules.question.schemas import OptionImportItem, QuestionImportItem


# ── Helpers ───────────────────────────────────────────────────────────────────

def text_options(count=4) -> list[OptionImportItem]:
    """4 valid text options."""
    return [OptionImportItem(option_no=i, text_en=f"Option {i}") for i in range(1, count + 1)]


def image_options(count=4) -> list[OptionImportItem]:
    """4 valid image options."""
    return [OptionImportItem(option_no=i, image_url=f"https://cdn/opt{i}.png") for i in range(1, count + 1)]


def marathi_options(count=4) -> list[OptionImportItem]:
    """4 valid marathi-only options."""
    return [OptionImportItem(option_no=i, text_mr=f"पर्याय {i}") for i in range(1, count + 1)]


def make_question(**kwargs) -> QuestionImportItem:
    defaults = dict(
        section_id=1,
        topic_id=1,
        question_no=1,
        question_type="text",
        text_en="What is 2+2?",
        correct_option=1,
        options=text_options(),
    )
    defaults.update(kwargs)
    return QuestionImportItem(**defaults)


# ── Test: text type ───────────────────────────────────────────────────────────

class TestTextQuestion:
    def test_validate_text_question_passes(self):
        q = make_question(question_type="text", text_en="What is 2+2?", options=text_options())
        errors = validate_question_import(q)
        assert errors == []

    def test_text_question_requires_text_en(self):
        q = make_question(question_type="text", text_en=None, options=text_options())
        errors = validate_question_import(q)
        assert any("text_en" in e for e in errors)

    def test_text_options_require_text_en(self):
        opts = [OptionImportItem(option_no=i, text_en=None) for i in range(1, 5)]
        q = make_question(question_type="text", options=opts)
        errors = validate_question_import(q)
        assert len([e for e in errors if "text_en" in e]) == 4


# ── Test: marathi_only type ───────────────────────────────────────────────────

class TestMarathiOnlyQuestion:
    def test_validate_marathi_only_requires_mr_text(self):
        q = make_question(
            question_type="marathi_only",
            text_en=None,
            text_mr=None,
            options=marathi_options(),
        )
        errors = validate_question_import(q)
        assert any("text_mr" in e for e in errors)

    def test_marathi_only_passes_with_text_mr(self):
        q = make_question(
            question_type="marathi_only",
            text_en=None,
            text_mr="हे काय आहे?",
            options=marathi_options(),
        )
        errors = validate_question_import(q)
        assert errors == []

    def test_marathi_only_rejects_text_en(self):
        q = make_question(
            question_type="marathi_only",
            text_en="Some english",
            text_mr="हे काय आहे?",
            options=marathi_options(),
        )
        errors = validate_question_import(q)
        assert any("text_en" in e for e in errors)

    def test_marathi_only_options_require_text_mr(self):
        opts = [OptionImportItem(option_no=i, text_en=f"Eng {i}") for i in range(1, 5)]
        q = make_question(
            question_type="marathi_only",
            text_en=None,
            text_mr="प्रश्न?",
            options=opts,
        )
        errors = validate_question_import(q)
        assert any("text_mr" in e for e in errors)


# ── Test: image_only type ─────────────────────────────────────────────────────

class TestImageOnlyQuestion:
    def test_validate_image_only_requires_image_url(self):
        q = make_question(
            question_type="image_only",
            text_en=None,
            text_mr=None,
            question_image_url=None,
            context_ref=None,
            options=image_options(),
        )
        errors = validate_question_import(q)
        assert any("image_url" in e or "context_ref" in e for e in errors)

    def test_image_only_passes_with_image_url(self):
        q = make_question(
            question_type="image_only",
            text_en=None,
            text_mr=None,
            question_image_url="https://cdn/q1.png",
            options=image_options(),
        )
        errors = validate_question_import(q)
        assert errors == []

    def test_image_only_passes_with_context_ref(self):
        q = make_question(
            question_type="image_only",
            text_en=None,
            text_mr=None,
            question_image_url=None,
            context_ref=0,
            options=image_options(),
        )
        errors = validate_question_import(q)
        assert errors == []

    def test_image_only_rejects_text_en(self):
        q = make_question(
            question_type="image_only",
            text_en="Should not be here",
            text_mr=None,
            question_image_url="https://cdn/q.png",
            options=image_options(),
        )
        errors = validate_question_import(q)
        assert any("text_en" in e for e in errors)

    def test_image_only_options_require_image_url(self):
        q = make_question(
            question_type="image_only",
            text_en=None,
            text_mr=None,
            question_image_url="https://cdn/q.png",
            options=text_options(),  # wrong — should be image options
        )
        errors = validate_question_import(q)
        assert any("image_url" in e for e in errors)


# ── Test: context_text type ───────────────────────────────────────────────────

class TestContextTextQuestion:
    def test_context_text_requires_context_ref(self):
        q = make_question(
            question_type="context_text",
            text_en="Based on the passage...",
            context_ref=None,
            options=text_options(),
        )
        errors = validate_question_import(q)
        assert any("context_ref" in e for e in errors)

    def test_context_text_passes_with_context_ref(self):
        q = make_question(
            question_type="context_text",
            text_en="Based on the passage...",
            context_ref=0,
            options=text_options(),
        )
        errors = validate_question_import(q)
        assert errors == []


# ── Test: bilingual type ──────────────────────────────────────────────────────

class TestBilingualQuestion:
    def test_bilingual_requires_both_languages(self):
        q = make_question(
            question_type="bilingual",
            text_en="What is?",
            text_mr=None,
            options=text_options(),
        )
        errors = validate_question_import(q)
        assert any("text_mr" in e for e in errors)

    def test_bilingual_passes_with_both_languages(self):
        q = make_question(
            question_type="bilingual",
            text_en="What is?",
            text_mr="काय आहे?",
            options=text_options(),
        )
        errors = validate_question_import(q)
        assert errors == []


# ── Test: universal rules ─────────────────────────────────────────────────────

class TestUniversalRules:
    def test_validate_wrong_option_count_fails(self):
        q = make_question(options=text_options(count=3))  # only 3 options
        errors = validate_question_import(q)
        assert any("4 options" in e for e in errors)

    def test_validate_correct_option_out_of_range_fails(self):
        q = make_question(correct_option=5)  # must be 1-4
        errors = validate_question_import(q)
        assert any("correct_option" in e for e in errors)

    def test_validate_correct_option_zero_fails(self):
        q = make_question(correct_option=0)
        errors = validate_question_import(q)
        assert any("correct_option" in e for e in errors)

    def test_unknown_question_type_fails(self):
        q = make_question(question_type="invalid_type")
        errors = validate_question_import(q)
        assert any("unknown" in e.lower() for e in errors)

    def test_duplicate_option_nos_detected(self):
        opts = [OptionImportItem(option_no=1, text_en=f"Opt {i}") for i in range(4)]
        q = make_question(options=opts)
        errors = validate_question_import(q)
        assert any("option_no" in e for e in errors)
