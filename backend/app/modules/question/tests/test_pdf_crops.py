"""
Regression tests for PDF figure-crop extraction.

Context: a 2026-08-17 content audit found the crop extractor was capturing the
whole question block — stem, figure AND all four options — into one PNG. Because
the stem and options are also stored as text and rendered separately, students
saw every question twice: once as real controls, once as an unclickable image.
Plain text questions with no figure at all (e.g. exam 16 Q1) got a redundant crop.

These tests pin the corrected behaviour: crop the figure band only, and produce
no crop when there is no figure.
"""

import fitz
import pytest

from app.modules.question.pdf_importer import (
    _OPTION_LINE_RE,
    extract_question_crops_from_pdf_bytes,
)


def _page_with(doc, draw):
    """Importer skips page 0 (cover), so content always goes on page 1+."""
    if doc.page_count == 0:
        doc.new_page()
    page = doc.new_page(width=595, height=842)
    draw(page)
    return page


def _text_only_question(page):
    page.insert_text((50, 110), "01.", fontsize=11)
    page.insert_text((90, 110), "Which letters make a meaningful word?", fontsize=11)
    page.insert_text((90, 132), "(1) Excercise  (2) Excersize  (3) Exercise  (4) Exersize", fontsize=11)


def _question_with_figure(page):
    page.insert_text((50, 170), "02.", fontsize=11)
    page.insert_text((90, 170), "Look at the picture and pick the odd one.", fontsize=11)
    page.draw_circle(fitz.Point(300, 225), 32, color=(0, 0, 0), width=1.5)
    page.draw_rect(fitz.Rect(360, 195, 420, 255), color=(0, 0, 0), width=1.5)
    page.insert_text((90, 290), "(1) Bird  (2) Branch  (3) Grass  (4) River", fontsize=11)


def _build_pdf(*drawers) -> bytes:
    doc = fitz.open()

    def draw_all(page):
        for drawer in drawers:
            drawer(page)

    _page_with(doc, draw_all)
    return doc.tobytes()


def _pixels(png_bytes: bytes):
    pix = fitz.Pixmap(png_bytes)
    return pix.width, pix.height


def test_text_only_question_produces_no_crop():
    """A question with no figure must not get an image attached."""
    crops = extract_question_crops_from_pdf_bytes(_build_pdf(_text_only_question))
    assert 1 not in crops


def test_question_with_figure_produces_a_crop():
    crops = extract_question_crops_from_pdf_bytes(_build_pdf(_question_with_figure))
    assert 2 in crops
    assert crops[2][:8] == b"\x89PNG\r\n\x1a\n"


def test_crop_excludes_stem_and_options():
    """
    The crop must cover only the figure band. Regression guard for the whole-block
    crop that duplicated the stem text and all four options into the image.
    """
    pdf = _build_pdf(_question_with_figure)
    crops = extract_question_crops_from_pdf_bytes(pdf)
    _width, height = _pixels(crops[2])

    # Stem baseline y=170, options baseline y=290. The figure band between them
    # is ~100pt tall; rendered at 2x that is ~200px. A whole-block crop would
    # span header (y~164) to the next block and be substantially taller.
    assert height < 2 * (290 - 170), (
        f"crop height {height}px suggests stem/options were included"
    )


def test_crop_contains_the_figure_ink():
    """The isolated band must still hold the drawing, not be blank."""
    crops = extract_question_crops_from_pdf_bytes(_build_pdf(_question_with_figure))
    pix = fitz.Pixmap(crops[2])
    samples = pix.samples
    dark = sum(1 for idx in range(0, len(samples), pix.n) if samples[idx] < 200)
    assert dark > 0, "figure band rendered blank — the drawing was clipped out"


def test_mixed_page_only_crops_the_figure_question():
    """On a page with both kinds, only the figure question yields a crop."""
    crops = extract_question_crops_from_pdf_bytes(
        _build_pdf(_text_only_question, _question_with_figure)
    )
    assert sorted(crops) == [2]


@pytest.mark.parametrize(
    "line",
    [
        "(1) Bird  (2) Branch",
        "(१) A  (२) B",          # Marathi papers use Devanagari numerals
        "1) first option",
        "[3] bracketed",
        "4. dotted",
        "  (2)   leading whitespace",
    ],
)
def test_option_line_markers_are_recognised(line):
    """
    The figure band is bounded by the first option marker, so every marker style
    the papers use must match. Tested directly rather than through a rendered
    PDF: the default base-14 font cannot encode Devanagari, so a fixture would
    silently render (१) as (·) and test the font, not the parser.
    """
    assert _OPTION_LINE_RE.match(line)


@pytest.mark.parametrize(
    "line",
    [
        "Look at the picture and pick the odd one.",
        "5) out of range",
        "Section - II",
    ],
)
def test_non_option_lines_are_not_treated_as_markers(line):
    assert not _OPTION_LINE_RE.match(line)


def test_empty_pdf_yields_no_crops():
    doc = fitz.open()
    doc.new_page()
    assert extract_question_crops_from_pdf_bytes(doc.tobytes()) == {}
