"""
Reusable PDF exam importer for MSCE-style papers.

The importer is review-first. It extracts question text/options, reads the
answer-key table, builds a BulkImportSchema, and reports any unsafe rows before
the service writes to Supabase.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

import fitz

from app.modules.question.legacy_marathi import (
    convert_shree_dev_0708e_to_unicode,
    devanagari_digit_to_ascii,
    has_shree_dev_artifacts,
    normalize_text,
)
from app.modules.question.schemas import (
    BulkImportSchema,
    OptionImportItem,
    QuestionImportItem,
)


LanguageStrategy = Literal["auto", "bilingual", "english", "marathi"]
AnswerSet = Literal["A", "B", "C", "D"]


@dataclass
class ExtractedPdfQuestion:
    question_no: int
    text: str
    options: list[str]


@dataclass
class PdfImportPreviewQuestion:
    question_no: int
    question_type: str
    correct_option: int | None
    is_cancelled: bool = False
    cancelled_reason: str | None = None
    text_en: str | None = None
    text_mr: str | None = None
    options_en: list[str] = field(default_factory=list)
    options_mr: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class PdfImportBuildResult:
    payload: BulkImportSchema | None
    preview: list[PdfImportPreviewQuestion]
    warnings: list[str]
    errors: list[str]
    key_count: int
    cancelled_questions: list[int]
    question_image_assets: dict[int, bytes] = field(default_factory=dict)


def clean_pdf_text(text_value: str) -> str:
    text_value = re.sub(r"SPACE FOR ROUGH WORK.*?(?=\n\s*\d+\.|\Z)", "", text_value, flags=re.S)
    text_value = re.sub(r"^\s*\d{4}-Marathi Set-A\s*$", "", text_value, flags=re.M)
    text_value = re.sub(r"^\s*(?:Contd\.\.\.|P\.T\.O\.)\s*$", "", text_value, flags=re.M)
    text_value = re.sub(r"^\s*कच्च्या कामासाठी फक्त\s*$", "", text_value, flags=re.M)
    text_value = re.sub(r"\bP\.T\.O\.\b", "", text_value)
    text_value = re.sub(r"\bContd\.\.\.", "", text_value)
    text_value = re.sub(r"\b\d+\s+of\s+\d+\b", "", text_value)
    text_value = re.sub(r"0\s*5\s*[012]\s*[12]", "", text_value)
    text_value = re.sub(r"CCC_05[012][12].*", "", text_value)
    return text_value


def strip_following_instruction_block(question_text: str) -> str:
    patterns = [
        r"\n\s*Instruction\s+for\s+Question\s+No\.?\s*0?\d+(?:\s+and\s+0?\d+)?\..*",
        r"\n\s*àíZ H«\$\.\s*0?\d+\s+Vo\s+0?\d+\s+gmR>r\s+gyMZm\s*-.*",
        r"\n\s*प्रश्न क्र\.\s*[०0]?[१-९1-9]\d*\s+ते\s+[०0]?[१-९1-9]\d*\s+साठी\s+सूचना\s*-.*",
        r"\n\s*Question\s+No\.?\s*0?\d+\s+to\s+0?\d+.*",
        r"\n\s*SECTION\s*-\s*II.*",
        r"\n\s*विभाग\s*-\s*II.*",
    ]
    for pattern in patterns:
        question_text = re.sub(pattern, "", question_text, flags=re.S | re.I)
    return question_text


def split_options(question_text: str) -> tuple[str, list[str]]:
    question_text = strip_following_instruction_block(question_text)
    marker = re.compile(r"(?:^|\s)\(([1-4१-४])\)\s*")
    matches = list(marker.finditer(question_text))
    if len(matches) < 4:
        marker = re.compile(r"(?:^|\s)([1-4१-४])\)\s*")
        matches = list(marker.finditer(question_text))
    if len(matches) < 4:
        return normalize_text(question_text), []

    stem = normalize_text(question_text[: matches[0].start()])
    options: list[str] = []
    for idx, match in enumerate(matches[:4]):
        start = match.end()
        end = matches[idx + 1].start() if idx < 3 else len(question_text)
        options.append(normalize_text(strip_following_instruction_block(question_text[start:end])))
    return stem, options


def extract_page_text(page: fitz.Page, *, convert_legacy_marathi: bool) -> str:
    if not convert_legacy_marathi:
        return page.get_text("text")

    raw = page.get_text("rawdict")
    lines: list[tuple[float, float, str]] = []
    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = sorted(line.get("spans", []), key=lambda span: span.get("bbox", [0, 0, 0, 0])[0])
            parts: list[str] = []
            last_x1: float | None = None
            for span in spans:
                bbox = span.get("bbox", [0, 0, 0, 0])
                if last_x1 is not None and float(bbox[0]) - last_x1 > 8 and parts and not parts[-1].endswith(" "):
                    parts.append(" ")
                span_text = "".join(char.get("c", "") for char in span.get("chars", []))
                if "SHREE" in span.get("font", ""):
                    span_text = convert_shree_dev_0708e_to_unicode(span_text)
                parts.append(span_text)
                last_x1 = float(bbox[2])
            line_text = "".join(parts).strip()
            if line_text:
                bbox = line.get("bbox", [0, 0, 0, 0])
                lines.append((float(bbox[1]), float(bbox[0]), line_text))
    lines.sort(key=lambda item: (round(item[0], 1), item[1]))
    return "\n".join(line for _y, _x, line in lines)


def extract_questions_from_pdf_bytes(pdf_bytes: bytes, *, convert_legacy_marathi: bool) -> dict[int, ExtractedPdfQuestion]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts: list[str] = []
    for page_index, page in enumerate(doc):
        if page_index == 0:
            continue
        page_text = clean_pdf_text(extract_page_text(page, convert_legacy_marathi=convert_legacy_marathi))
        text_parts.append(page_text)

    full_text = "\n".join(text_parts)
    q_re = re.compile(
        r"(?:^|\n)\s*(?:0?([1-9]|[1-6][0-9]|7[0-5])|०?([१-९]|[१-६][०-९]|७[०-५]))\.\s+",
        re.M,
    )
    scan_text = "\n" + full_text
    matches = list(q_re.finditer(scan_text))
    questions: dict[int, ExtractedPdfQuestion] = {}
    for idx, match in enumerate(matches):
        q_no = int(devanagari_digit_to_ascii(match.group(1) or match.group(2)))
        start = max(match.end() - 1, 0)
        end = matches[idx + 1].start() - 1 if idx + 1 < len(matches) else len(full_text)
        if not 1 <= q_no <= 75:
            continue
        stem, options = split_options(normalize_text(full_text[start:end]))
        questions[q_no] = ExtractedPdfQuestion(q_no, stem, options)
    return questions


def extract_answer_key_from_pdf_bytes(pdf_bytes: bytes, answer_set: AnswerSet = "A") -> tuple[dict[int, int], list[int], list[str]]:
    text_key = _extract_text_answer_key(pdf_bytes, answer_set)
    if text_key[0]:
        return text_key
    return _extract_image_answer_key(pdf_bytes, answer_set)


def _extract_text_answer_key(pdf_bytes: bytes, answer_set: AnswerSet) -> tuple[dict[int, int], list[int], list[str]]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = "\n".join(page.get_text("text") for page in doc)
    if not text.strip():
        return {}, [], ["Answer key PDF has no extractable text; using image-table parser"]
    warnings = ["Answer key PDF text extraction is not implemented for this layout; using image-table parser"]
    return {}, [], warnings


def _extract_image_answer_key(pdf_bytes: bytes, answer_set: AnswerSet) -> tuple[dict[int, int], list[int], list[str]]:
    try:
        import cv2
        import numpy as np
    except Exception as exc:  # pragma: no cover - deployment dependency guard
        return {}, [], [f"opencv-python-headless and numpy are required for image answer-key parsing: {exc}"]

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if doc.page_count == 0:
        return {}, [], ["Answer key PDF has no pages"]

    pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if pix.n >= 3 else image
    _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    blocks = _detect_answer_key_blocks(cv2, threshold)
    y_lines = _detect_answer_key_row_lines(cv2, threshold)
    warnings: list[str] = []
    if len(blocks) != 3 or len(y_lines) < 26:
        return {}, [], [f"Could not detect answer-key grid reliably (blocks={len(blocks)}, row_lines={len(y_lines)})"]

    y_lines = y_lines[:26]
    digit_templates = _build_digit_templates(cv2, np, gray, blocks, y_lines)
    if not all(digit_templates.get(str(value)) for value in range(1, 5)):
        return {}, [], ["Could not build answer-key digit templates from question-number column"]

    set_index = "ABCD".index(answer_set)
    keys: dict[int, int] = {}
    cancelled: list[int] = []

    for block_idx, block in enumerate(blocks):
        for row_idx in range(25):
            q_no = block_idx * 25 + row_idx + 1
            crop = gray[y_lines[row_idx] : y_lines[row_idx + 1], block[1 + set_index] : block[2 + set_index]]
            value = _classify_answer_cell(cv2, np, crop, digit_templates)
            if value == "*":
                cancelled.append(q_no)
            elif value in {"1", "2", "3", "4"}:
                keys[q_no] = int(value)
            else:
                warnings.append(f"Could not read answer key for Q{q_no}")

    return keys, cancelled, warnings


def _detect_answer_key_blocks(cv2, threshold) -> list[list[int]]:
    vertical = cv2.morphologyEx(
        threshold,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50)),
        iterations=1,
    )
    contours, _ = cv2.findContours(vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    x_values = sorted(
        cv2.boundingRect(contour)[0]
        for contour in contours
        if cv2.boundingRect(contour)[3] > threshold.shape[0] * 0.45
    )
    if len(x_values) < 18:
        return []
    return [x_values[idx : idx + 6] for idx in range(0, 18, 6)]


def _detect_answer_key_row_lines(cv2, threshold) -> list[int]:
    horizontal = cv2.morphologyEx(
        threshold,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1)),
        iterations=1,
    )
    contours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    y_values = sorted(
        cv2.boundingRect(contour)[1]
        for contour in contours
        if cv2.boundingRect(contour)[2] > threshold.shape[1] * 0.15
    )
    merged: list[int] = []
    for y_value in y_values:
        if not merged or y_value - merged[-1] > 5:
            merged.append(y_value)
    if not merged:
        return []
    return [y for y in merged if y >= merged[0] + 100][-26:]


def _build_digit_templates(cv2, np, gray, blocks: list[list[int]], y_lines: list[int]) -> dict[str, list]:
    templates: dict[str, list] = {str(value): [] for value in range(1, 5)}
    for block_idx, block in enumerate(blocks):
        for row_idx in range(25):
            q_no = block_idx * 25 + row_idx + 1
            crop = gray[y_lines[row_idx] : y_lines[row_idx + 1], block[0] : block[1]]
            components = _digit_components(cv2, crop)
            digits = str(q_no)
            if len(components) != len(digits):
                continue
            _, binary = cv2.threshold(crop[4:-4, 4:-4], 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            for digit, (x, y, width, height) in zip(digits, components):
                if digit in templates:
                    templates[digit].append(_normalize_glyph(cv2, np, binary[y : y + height, x : x + width]))
    return templates


def _digit_components(cv2, crop) -> list[tuple[int, int, int, int]]:
    _, binary = cv2.threshold(crop[4:-4, 4:-4], 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(binary, 8)
    components: list[tuple[int, int, int, int]] = []
    for idx in range(1, count):
        x, y, width, height, area = stats[idx]
        if area > 5 and height > 8 and width > 2:
            components.append((x, y, width, height))
    return sorted(components)


def _normalize_glyph(cv2, np, glyph):
    height, width = glyph.shape
    pad = 4
    size = max(height, width) + 2 * pad
    canvas = np.zeros((size, size), dtype=np.uint8)
    y_offset = (size - height) // 2
    x_offset = (size - width) // 2
    canvas[y_offset : y_offset + height, x_offset : x_offset + width] = glyph
    resized = cv2.resize(canvas, (32, 32), interpolation=cv2.INTER_AREA)
    return (resized > 64).astype(np.uint8)


def _classify_answer_cell(cv2, np, crop, templates: dict[str, list]) -> str | None:
    inner = crop[4:-4, 4:-4]
    _, binary = cv2.threshold(inner, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    y_values, x_values = np.where(binary > 0)
    if len(x_values) == 0:
        return None
    x0, x1 = x_values.min(), x_values.max()
    y0, y1 = y_values.min(), y_values.max()
    if y1 - y0 + 1 < 12:
        return "*"
    glyph = _normalize_glyph(cv2, np, binary[y0 : y1 + 1, x0 : x1 + 1])
    best_digit: str | None = None
    best_score = 999.0
    for digit, digit_templates in templates.items():
        for template in digit_templates:
            score = float(np.mean((glyph.astype(float) - template.astype(float)) ** 2))
            if score < best_score:
                best_digit = digit
                best_score = score
    return best_digit if best_score <= 0.18 else None


def build_pdf_import_payload(
    *,
    exam_id: int,
    language_strategy: LanguageStrategy,
    answer_set: AnswerSet,
    english_question_pdf: bytes | None,
    marathi_question_pdf: bytes | None,
    answer_key_pdf: bytes,
    section_topic_map: list[dict],
) -> PdfImportBuildResult:
    warnings: list[str] = []
    errors: list[str] = []

    if language_strategy == "auto" and english_question_pdf and marathi_question_pdf:
        errors.append(
            "Both English and Marathi PDFs were uploaded. Choose 'bilingual' only when they are translations of the same question set, "
            "or import them separately as English/Marathi medium exams."
        )
    if language_strategy in ("auto", "english") and not english_question_pdf and not marathi_question_pdf:
        errors.append("Upload at least one question paper PDF")
    if language_strategy == "english" and not english_question_pdf:
        errors.append("English import requires an English question paper PDF")
    if language_strategy == "marathi" and not marathi_question_pdf:
        errors.append("Marathi import requires a Marathi question paper PDF")
    if language_strategy == "bilingual" and (not english_question_pdf or not marathi_question_pdf):
        errors.append("Bilingual import requires both English and Marathi question paper PDFs")

    english_questions = (
        extract_questions_from_pdf_bytes(english_question_pdf, convert_legacy_marathi=False)
        if english_question_pdf
        else {}
    )
    english_image_assets = (
        extract_question_crops_from_pdf_bytes(english_question_pdf)
        if english_question_pdf
        else {}
    )
    marathi_questions = (
        extract_questions_from_pdf_bytes(marathi_question_pdf, convert_legacy_marathi=True)
        if marathi_question_pdf
        else {}
    )
    marathi_image_assets = (
        extract_question_crops_from_pdf_bytes(marathi_question_pdf)
        if marathi_question_pdf
        else {}
    )
    answer_key, cancelled_questions, key_warnings = extract_answer_key_from_pdf_bytes(answer_key_pdf, answer_set)
    warnings.extend(key_warnings)

    if language_strategy == "auto":
        language_strategy = "english" if english_questions else "marathi"

    section_lookup = _build_section_lookup(section_topic_map)
    question_numbers = _question_numbers_for_strategy(language_strategy, english_questions, marathi_questions)
    preview: list[PdfImportPreviewQuestion] = []
    import_questions: list[QuestionImportItem] = []
    question_image_assets: dict[int, bytes] = {}

    for q_no in sorted(question_numbers):
        en_q = english_questions.get(q_no)
        mr_q = marathi_questions.get(q_no)
        row_warnings: list[str] = []
        row_errors: list[str] = []
        correct_option = answer_key.get(q_no)
        is_cancelled = q_no in cancelled_questions
        cancelled_reason = "Cancelled in official answer key" if is_cancelled else None
        if correct_option is None and not is_cancelled:
            row_errors.append("Missing correct option from answer key")
        section_topic = section_lookup.get(q_no)
        if section_topic is None:
            row_errors.append("No section/topic mapping found for this question number")

        has_english_crop_fallback = (
            language_strategy == "english"
            and en_q is not None
            and len(en_q.options) == 0
            and q_no in english_image_assets
        )
        has_marathi_crop_fallback = (
            language_strategy == "marathi"
            and mr_q is not None
            and len(mr_q.options) == 0
            and q_no in marathi_image_assets
        )
        has_english_image_fallback = (
            language_strategy == "english"
            and en_q is not None
            and not en_q.text
            and q_no in english_image_assets
        )
        has_marathi_image_fallback = (
            language_strategy == "marathi"
            and mr_q is not None
            and not mr_q.text
            and q_no in marathi_image_assets
        )
        has_english_legacy_crop_fallback = (
            language_strategy == "english"
            and en_q is not None
            and (
                has_shree_dev_artifacts(en_q.text)
                or any(has_shree_dev_artifacts(option) for option in en_q.options)
            )
            and q_no in english_image_assets
        )
        if en_q and len(en_q.options) != 4 and not has_english_crop_fallback:
            row_errors.append(f"English extraction found {len(en_q.options)} options")
        if mr_q and len(mr_q.options) != 4 and not has_marathi_crop_fallback:
            row_errors.append(f"Marathi extraction found {len(mr_q.options)} options")
        if mr_q and (has_shree_dev_artifacts(mr_q.text) or any(has_shree_dev_artifacts(option) for option in mr_q.options)):
            row_errors.append("Marathi extraction still contains legacy Shree Dev artifacts")

        has_crop_fallback = (
            has_english_crop_fallback
            or has_marathi_crop_fallback
            or has_english_image_fallback
            or has_marathi_image_fallback
            or has_english_legacy_crop_fallback
        )
        question_type = "text_image" if has_crop_fallback else _question_type_for(language_strategy, en_q, mr_q)
        preview.append(PdfImportPreviewQuestion(
            question_no=q_no,
            question_type=question_type,
            correct_option=correct_option,
            is_cancelled=is_cancelled,
            cancelled_reason=cancelled_reason,
            text_en=(
                en_q.text
                if en_q
                and en_q.text
                and language_strategy in ("english", "bilingual")
                and not has_english_legacy_crop_fallback
                else f"Question {q_no}" if has_english_image_fallback or has_english_legacy_crop_fallback else None
            ),
            text_mr=(
                mr_q.text
                if mr_q and mr_q.text and language_strategy in ("marathi", "bilingual")
                else f"प्रश्न {q_no}" if has_marathi_image_fallback else None
            ),
            options_en=(
                [f"Option {idx}" for idx in range(1, 5)]
                if has_english_crop_fallback or has_english_legacy_crop_fallback
                else en_q.options if en_q and language_strategy in ("english", "bilingual") else []
            ),
            options_mr=(
                [f"पर्याय {idx}" for idx in range(1, 5)]
                if has_marathi_crop_fallback
                else mr_q.options if mr_q and language_strategy in ("marathi", "bilingual") else []
            ),
            warnings=[*row_errors, *row_warnings],
        ))

        if row_errors:
            errors.extend(f"Q{q_no}: {error}" for error in row_errors)
            continue

        text_en = (
            en_q.text
            if en_q
            and en_q.text
            and language_strategy in ("english", "bilingual")
            and not has_english_legacy_crop_fallback
            else f"Question {q_no}" if has_english_image_fallback or has_english_legacy_crop_fallback else None
        )
        text_mr = (
            mr_q.text
            if mr_q and mr_q.text and language_strategy in ("marathi", "bilingual")
            else f"प्रश्न {q_no}" if has_marathi_image_fallback else None
        )
        options = []
        for option_idx in range(4):
            options.append(OptionImportItem(
                option_no=option_idx + 1,
                text_en=(
                    f"Option {option_idx + 1}"
                    if has_english_crop_fallback or has_english_legacy_crop_fallback
                    else en_q.options[option_idx] if en_q and language_strategy in ("english", "bilingual") else None
                ),
                text_mr=(
                    f"पर्याय {option_idx + 1}"
                    if has_marathi_crop_fallback
                    else mr_q.options[option_idx] if mr_q and language_strategy in ("marathi", "bilingual") else None
                ),
            ))
        if has_english_crop_fallback or has_english_image_fallback or has_english_legacy_crop_fallback:
            question_image_assets[q_no] = english_image_assets[q_no]
        if has_marathi_crop_fallback or has_marathi_image_fallback:
            question_image_assets[q_no] = marathi_image_assets[q_no]
        import_questions.append(QuestionImportItem(
            section_id=section_topic["section_id"],
            topic_id=section_topic["topic_id"],
            question_no=q_no,
            question_type=question_type,
            text_en=text_en,
            text_mr=text_mr,
            question_image_url=f"pending://pdf-import/exams/{exam_id}/questions/{q_no}.png" if has_crop_fallback else None,
            question_image_alt_en=f"Question {q_no} figure" if has_english_crop_fallback or has_english_image_fallback or has_english_legacy_crop_fallback else None,
            question_image_alt_mr=f"प्रश्न {q_no} आकृती" if has_marathi_crop_fallback or has_marathi_image_fallback else None,
            correct_option=correct_option,
            is_cancelled=is_cancelled,
            cancelled_reason=cancelled_reason,
            marks=2,
            difficulty="medium",
            tags=["pdf_import"],
            options=options,
        ))

    payload = BulkImportSchema(exam_id=exam_id, contexts=[], questions=import_questions) if not errors else None
    return PdfImportBuildResult(
        payload=payload,
        preview=preview,
        warnings=warnings,
        errors=errors,
        key_count=len(answer_key),
        cancelled_questions=cancelled_questions,
        question_image_assets=question_image_assets,
    )


_OPTION_LINE_RE = re.compile(r"^\s*[\(\[]?\s*([1-4१-४])\s*[\)\].]\s*")

# A crop band this short holds no real figure — just leading/trailing whitespace.
_MIN_FIGURE_BAND_HEIGHT = 12.0
# Ink coverage below this is stray marks (rule lines, speckle), not a figure.
_MIN_FIGURE_INK_RATIO = 0.0015


def _question_line_boxes(page: fitz.Page) -> list[tuple[float, float, str]]:
    """Return (y_top, y_bottom, text) for every text line on the page, in order."""
    lines: list[tuple[float, float, str]] = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            text_value = "".join(
                span.get("text", "") for span in line.get("spans", [])
            ).strip()
            if not text_value:
                continue
            bbox = line.get("bbox", [0, 0, 0, 0])
            lines.append((float(bbox[1]), float(bbox[3]), text_value))
    lines.sort(key=lambda item: item[0])
    return lines


def _figure_band(
    page: fitz.Page,
    y_start: float,
    y_end: float,
) -> tuple[float, float] | None:
    """
    Find the vertical band holding a question's figure.

    The band runs from the bottom of the last stem line to the top of the first
    option line ``(1)``. Everything above is the stem and everything below is
    the options — both are already stored as text, so including them in the crop
    duplicates content the student can read and click natively.

    Falls back to the full question block when no option marker is found, which
    is the case for figure-only items whose options are themselves drawings.
    """
    lines = [line for line in _question_line_boxes(page) if y_start <= line[0] < y_end]
    if not lines:
        return None

    first_option_idx = next(
        (idx for idx, (_top, _bottom, text) in enumerate(lines) if _OPTION_LINE_RE.match(text)),
        None,
    )
    if first_option_idx is None:
        # No parseable options: keep the whole block (minus the header line).
        return lines[0][1], y_end
    if first_option_idx == 0:
        # Options start immediately — no room for a figure.
        return None

    stem_bottom = max(line[1] for line in lines[:first_option_idx])
    option_top = lines[first_option_idx][0]
    return stem_bottom, option_top


def _band_has_ink(page: fitz.Page, rect: fitz.Rect) -> bool:
    """
    True when the band contains meaningful non-white pixels.

    Guards against attaching a blank crop to a plain text question, which is how
    exam 16 Q1 (a pure text item) ended up with a redundant full-row image.
    """
    if rect.is_empty or rect.height < _MIN_FIGURE_BAND_HEIGHT:
        return False
    pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), clip=rect, alpha=False)
    if pix.width == 0 or pix.height == 0:
        return False
    samples = pix.samples
    stride = max(pix.n, 1)
    dark = sum(1 for idx in range(0, len(samples), stride) if samples[idx] < 200)
    total = max(pix.width * pix.height, 1)
    return (dark / total) >= _MIN_FIGURE_INK_RATIO


def extract_question_crops_from_pdf_bytes(pdf_bytes: bytes) -> dict[int, bytes]:
    """
    Render image crops for the figure region of questions whose diagrams are
    vector drawings rather than extractable text.

    The crop is clipped to the figure band between the stem text and the first
    option marker. It deliberately excludes the stem and the options: both are
    stored as text and rendered separately by the client, so a whole-block crop
    shows the student the same question text and the same four options twice —
    once as an unclickable image and once as real controls.

    Questions with no ink in the figure band produce no crop at all.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    crops: dict[int, bytes] = {}
    q_re = re.compile(r"^\s*0?([1-9]|[1-6][0-9]|7[0-5])\.\s*")

    for page_index, page in enumerate(doc):
        if page_index == 0:
            continue
        starts: list[tuple[int, float]] = []
        for block in page.get_text("dict").get("blocks", []):
            if block.get("type") != 0:
                continue
            text_value = " ".join(
                span.get("text", "")
                for line in block.get("lines", [])
                for span in line.get("spans", [])
            )
            match = q_re.match(text_value)
            if match:
                starts.append((int(match.group(1)), float(block["bbox"][1])))

        starts.sort(key=lambda item: item[1])
        for idx, (q_no, y0) in enumerate(starts):
            block_end = (
                starts[idx + 1][1] - 6
                if idx + 1 < len(starts)
                else min(page.rect.height - 60, y0 + 220)
            )
            if block_end <= y0 + 10:
                continue

            band = _figure_band(page, y0, block_end)
            if band is None:
                continue
            band_top, band_bottom = band
            if band_bottom - band_top < _MIN_FIGURE_BAND_HEIGHT:
                continue

            # band_top is already a line's bottom edge and band_bottom a line's
            # top edge, so pad inward to keep descenders/ascenders of the
            # neighbouring text out of the crop.
            rect = fitz.Rect(
                40,
                max(0.0, band_top + 1),
                page.rect.width - 30,
                min(page.rect.height - 40, band_bottom - 1),
            )
            if not _band_has_ink(page, rect):
                continue
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=rect, alpha=False)
            crops[q_no] = pix.tobytes("png")
    return crops


def _question_numbers_for_strategy(
    language_strategy: LanguageStrategy,
    english_questions: dict[int, ExtractedPdfQuestion],
    marathi_questions: dict[int, ExtractedPdfQuestion],
) -> set[int]:
    if language_strategy == "english":
        return set(english_questions)
    if language_strategy == "marathi":
        return set(marathi_questions)
    return set(english_questions) | set(marathi_questions)


def _question_type_for(
    language_strategy: LanguageStrategy,
    en_q: ExtractedPdfQuestion | None,
    mr_q: ExtractedPdfQuestion | None,
) -> str:
    if language_strategy == "marathi" and not en_q:
        return "marathi_only"
    if language_strategy == "bilingual" and en_q and mr_q:
        return "bilingual"
    return "text"


def _build_section_lookup(section_topic_map: list[dict]) -> dict[int, dict]:
    lookup: dict[int, dict] = {}
    for row in section_topic_map:
        for q_no in range(int(row["question_from"]), int(row["question_to"]) + 1):
            lookup[q_no] = {
                "section_id": int(row["section_id"]),
                "topic_id": int(row["topic_id"]),
            }
    return lookup
