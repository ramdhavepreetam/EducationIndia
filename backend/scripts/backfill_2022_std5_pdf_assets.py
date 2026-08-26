#!/usr/bin/env python3
"""
Build and optionally apply a 2022 Std 5 bilingual/image backfill manifest.

Default mode is review-only. It reads the four local PDFs, reads the existing
Supabase rows for exams 16/17, writes a manifest plus QA HTML/CSV, and renders
candidate image crops. It does not upload to R2 or update the DB unless an
explicit --apply-* flag is passed.

Example:
    python backend/scripts/backfill_2022_std5_pdf_assets.py
    python backend/scripts/backfill_2022_std5_pdf_assets.py --apply-text
    python backend/scripts/backfill_2022_std5_pdf_assets.py --apply-images
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import html
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

import aioboto3
import fitz  # PyMuPDF
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "generated" / "msce_2022_std5_backfill"
DEFAULT_TEST_DIR = Path("/Users/preetam/Desktop/Test")

EXAMS = {
    "501": {
        "exam_id": 16,
        "english_pdf": "Question_PaperFeb_2022/5th/English_Paper1.pdf",
        "marathi_pdf": "Question_PaperFeb_2022/5th/Marathi_Paper1.pdf",
    },
    "502": {
        "exam_id": 17,
        "english_pdf": "Question_PaperFeb_2022/5th/English_Paper2.pdf",
        "marathi_pdf": "Question_PaperFeb_2022/5th/Marathi_Paper2.pdf",
    },
}

MANUAL_CROP_OVERRIDES = {
    # Paper 501 Q06: generic question-region detection included the rough-work
    # band at the bottom. Keep the full prompt, figure, and answer labels only.
    ("501", 6): (1, (30.0, 421.49310302734375, 547.6539306640625, 586.0)),
}

MANUAL_NO_IMAGE = {
    # These are shared-passage/context questions. The generic detector marked
    # them because phrases like "given object" or "following line" look like
    # image prompts, but the source PDF has no standalone question image here.
    ("501", 14),
    ("501", 15),
    ("501", 21),
    ("501", 22),
}

# MSCE Paper 501 Section I is the first-language section. English and Marathi
# PDFs are not translations of the same questions here, so these rows cannot be
# merged into the same question IDs without separate answer keys/question rows.
DO_NOT_MERGE_LANGUAGE_SPECIFIC_RANGES = {
    "501": [(1, 25)],
}

IMAGE_HINTS_EN = (
    "picture",
    "figure",
    "diagram",
    "object",
    "chart",
    "graph",
    "image",
    "map",
    "given below",
    "following",
    "look at",
    "shown",
    "select the mirror",
    "water image",
)
IMAGE_HINTS_MR = (
    "चित्र",
    "आकृती",
    "खालील",
    "चौकट",
    "आरसा",
    "पाण्यातील",
    "नकाशा",
)

# The 2022 Marathi PDFs embed legacy Shree Dev 0708/0708E fonts. PyMuPDF
# extracts the legacy glyph codes, not Unicode Marathi, so text must be
# converted before it is safe to write into text_mr/options.text_mr.
#
# Base map: unicode-bunny 1.0.2 Shree 0708 mapping (MIT package). The E-font
# PDFs also use a few alternate glyph slots; those are added below.
SHREE_DEV_0708_UNICODE_TO_LEGACY = {
    "अ": "A",
    "आ": "Am",
    "इ": "B",
    "ई": "B©",
    "उ": "C",
    "ऊ": "D$",
    "ऋ": "F$",
    "ऌ": "ऌ",
    "ऍ": "E°",
    "ऎ": "ऎ",
    "ए": "E",
    "ऐ": "Eo",
    "ऑ": "Am°",
    "ऒ": "ऒ",
    "ओ": "Amo",
    "औ": "Am¡",
    "ं": "§",
    "ः": "…",
    "ँ": "±",
    "क": "H$",
    "ख": "I",
    "ग": "J",
    "घ": "K",
    "ङ": "L>",
    "च": "M",
    "छ": "N>",
    "ज": "O",
    "झ": "P",
    "ञ": "Äm",
    "ट": "Q>",
    "ठ": "R>",
    "ड": "S>",
    "ढ": "T>",
    "ण": "U",
    "त": "V",
    "थ": "W",
    "द": "X",
    "ध": "Y",
    "न": "Z",
    "प": "n",
    "फ": "\\$",
    "ब": "~",
    "भ": "^",
    "म": "_",
    "य": "`",
    "र": "a",
    "ऱ": "µa",
    "ल": "b",
    "ळ": "i",
    "ऴ": "µi",
    "व": "d",
    "श": "e",
    "ष": "f",
    "स": "g",
    "ह": "h",
    "क्ष": "j",
    "ज्ञ": "k",
    "ा": "m",
    "ि": "{",
    "ी": "r",
    "ु": "w",
    "ू": "y",
    "ृ": "¥",
    "ॅ": "°",
    "े": "o",
    "ै": "¡",
    "ॉ": "m°",
    "ो": "mo",
    "ौ": "m¡",
    "्": "²",
    "०": "0",
    "१": "1",
    "२": "2",
    "३": "3",
    "४": "4",
    "५": "5",
    "६": "6",
    "७": "7",
    "८": "8",
    "९": "9",
    "क्": "Š",
    "ख्": "»",
    "ग्": "½",
    "घ्": "¿",
    "ङ्": "L²>",
    "च्": "À",
    "छ्": "N²>",
    "ज्": "Á",
    "झ्": "Â",
    "ञ्": "Ä",
    "ट्": "Q²>",
    "ठ्": "R²>",
    "ड्": "S²>",
    "ढ्": "T²>",
    "ण्": "Ê",
    "त्": "Ë",
    "थ्": "Ï",
    "द्": "X²",
    "ध्": "Ü",
    "न्": "Ý",
    "प्": "ß",
    "फ्": "â",
    "ब्": "ã",
    "भ्": "ä",
    "म्": "å",
    "य्": "æ",
    "र्": "©",
    "ऱ्": "è",
    "ल्": "ë",
    "ळ्": "ù",
    "व्": "ì",
    "श्": "í",
    "ष्": "î",
    "स्": "ñ",
    "ह्": "ô",
    "क्ष्": "ú",
    "ज्ञ्": "k²",
    "त्र": "Ì",
    "त्त": "Îm",
    "न्न": "Þ",
    "द्द": "Ô",
    "द्ध": "Õ",
    "द्व": "Û",
    "द्य": "Ú",
    "द्म": "Ù",
    "न्ह": "Ýh",
    "म्ह": "åh",
    "ल्ह": "ëh",
    "व्ह": "ìh",
    "क्व": "¹$",
    "त्व": "Ëd",
    "स्व": "ñd",
    "प्र": "à",
    "क्र": "H«$",
    "ग्र": "J«",
    "द्र": "Ì",
    "ब्र": "Ð",
    "श्र": "~«",
    "स्र": "l",
    "ह्र": "ò",
    "प्ल": "õ",
    "क्ल": "ßb",
    "ग्ल": "Šb",
    "फ्ल": "½b",
    "श्ल": "âb",
    "स्ल": "íb",
}

SHREE_DEV_POST_RA = "\ue000"

SHREE_DEV_0708E_LEGACY_OVERRIDES = {
    "H¥$": "कृ",
    "Ho$": "के",
    "Hw$": "कु",
    "Hy$": "कू",
    "Q´>": "ट्र",
    "Sy>": "डू",
    "’w$": "फु",
    "’o$": "फे",
    "’$": "फ",
    "ê$": "रू",
    "é": "रू",
    "lr": "श्री",
    "á": "प्त",
    "³": "क्",
    "´": "्र",
    "«": "्र",
    "s": "ी",
    "Wu": "र्थी",
    "u": "ी",
    "t": "ीं",
    "q": "िं",
    "[": "ि",
    "¶": "य",
    "‘": "म",
    "þ": "ु",
    "ÿ": "ू",
    "ç": "्य",
    "ø": "ह्य",
    "ª": f"{SHREE_DEV_POST_RA}ं",
    "|": "ें",
    "pñd": "स्वी",
    "pñ": "स्",
    "D$": "ऊ",
    "D": "ऊ",
    ">": "",
}

SHREE_DEV_ALLOWED_PASSTHROUGH = set(" \n\t.,;:!?()\"'/-+=%")
SHREE_DEV_LEGACY_ARTIFACT_RE = re.compile(
    r"(?:H\$|[<>\[\]{}~`^¡¥§©ª«°²³´¶½ÀÂÊËÌÎÐÜÝÞßàáãåçèéêëìíîñúþÿ])"
)


def build_shree_dev_legacy_map() -> dict[str, str]:
    legacy_map: dict[str, str] = {}
    for unicode_text, legacy_text in SHREE_DEV_0708_UNICODE_TO_LEGACY.items():
        legacy_map.setdefault(legacy_text, unicode_text)
    # The public table maps this duplicate code to both त्र and द्र. In these
    # papers it is used for त्र in words such as मित्राला.
    legacy_map["Ì"] = "त्र"
    legacy_map["©"] = SHREE_DEV_POST_RA
    legacy_map.update(SHREE_DEV_0708E_LEGACY_OVERRIDES)
    return legacy_map


SHREE_DEV_0708E_LEGACY_TO_UNICODE = build_shree_dev_legacy_map()
SHREE_DEV_0708E_TOKENS = sorted(SHREE_DEV_0708E_LEGACY_TO_UNICODE, key=len, reverse=True)


def reorder_shree_dev_unicode(text_value: str) -> str:
    consonant = r"[\u0915-\u0939\u0958-\u095f]"
    marks = r"[\u093e-\u094c\u0901-\u0903\u0970]*"

    text_value = re.sub(r"ि(" + consonant + r"(?:्" + consonant + r")*)", r"\1ि", text_value)
    text_value = re.sub(r"िं(" + consonant + r"(?:्" + consonant + r")*)", r"\1िं", text_value)
    text_value = re.sub("(" + consonant + r")(ु|ू|ृ)्र", r"\1्र\2", text_value)
    text_value = re.sub(
        "(" + consonant + r"(?:्" + consonant + r")?)(" + marks + ")" + SHREE_DEV_POST_RA + r"([ंँ]?)",
        r"र्\1\2\3",
        text_value,
    )
    return text_value.replace(SHREE_DEV_POST_RA, "र्")


def convert_shree_dev_0708e_to_unicode(value: str | None) -> str:
    if not value:
        return ""

    output: list[str] = []
    idx = 0
    while idx < len(value):
        for token in SHREE_DEV_0708E_TOKENS:
            if value.startswith(token, idx):
                output.append(SHREE_DEV_0708E_LEGACY_TO_UNICODE[token])
                idx += len(token)
                break
        else:
            char = value[idx]
            if char in SHREE_DEV_ALLOWED_PASSTHROUGH or char.isdigit():
                output.append(char)
            elif char in {"\u2009", "\x07", "\r"}:
                output.append(" ")
            else:
                output.append(char)
            idx += 1

    converted = reorder_shree_dev_unicode("".join(output))
    converted = converted.replace("''", '"').replace("``", '"').replace("'", '"')
    converted = re.sub(r"[ \t]+", " ", converted)
    converted = re.sub(r"\s+\n", "\n", converted)
    return normalize_text(converted)


def has_shree_dev_artifacts(value: str | None) -> bool:
    return bool(value and SHREE_DEV_LEGACY_ARTIFACT_RE.search(value))


def devanagari_digit_to_ascii(value: str) -> str:
    return value.translate(str.maketrans("०१२३४५६७८९", "0123456789"))


@dataclass
class ExtractedQuestion:
    question_no: int
    text: str = ""
    options: list[str] = field(default_factory=list)
    page_index: int | None = None
    crop: tuple[float, float, float, float] | None = None


@dataclass
class DbOption:
    id: int
    option_no: int
    text_en: str | None
    text_mr: str | None
    image_url: str | None


@dataclass
class DbQuestion:
    id: int
    exam_id: int
    question_no: int
    question_type: str
    text_en: str | None
    text_mr: str | None
    question_image_url: str | None
    options: list[DbOption]


@dataclass
class ManifestItem:
    paper_code: str
    exam_id: int
    question_id: int
    question_no: int
    status: str
    current_question_type: str
    proposed_question_type: str
    current_text_en: str | None
    current_text_mr: str | None
    extracted_text_en: str | None
    extracted_text_mr: str | None
    extracted_options_en: list[str]
    extracted_options_mr: list[str]
    needs_image: bool
    crop_page: int | None
    crop_box: list[float] | None
    crop_preview: str | None
    crop_blank_score: float | None
    warnings: list[str] = field(default_factory=list)
    option_updates: list[dict[str, Any]] = field(default_factory=list)


def load_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for path in (PROJECT_ROOT / ".env", PROJECT_ROOT / "backend" / ".env"):
        if not path.exists():
            continue
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"').strip("'")
    values.update({k: v for k, v in os.environ.items() if v})
    return values


def db_url(env: dict[str, str]) -> str:
    url = env.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required in .env or environment")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.replace("\u00a0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def clean_pdf_text(text_value: str) -> str:
    text_value = re.sub(r"SPACE FOR ROUGH WORK.*?(?=\n\s*\d+\.|\Z)", "", text_value, flags=re.S)
    text_value = re.sub(r"^\s*\d{4}-Marathi Set-A\s*$", "", text_value, flags=re.M)
    text_value = re.sub(r"^\s*(?:Contd\.\.\.|P\.T\.O\.)\s*$", "", text_value, flags=re.M)
    text_value = re.sub(r"^\s*H\$ÀÀ¶m H\$m‘mgmR>r ’\$³V\s*$", "", text_value, flags=re.M)
    text_value = re.sub(r"^\s*कच्च्या कामासाठी फक्त\s*$", "", text_value, flags=re.M)
    text_value = re.sub(r"\bP\.T\.O\.\b", "", text_value)
    text_value = re.sub(r"\bContd\.\.\.", "", text_value)
    text_value = re.sub(r"\b\d+\s+of\s+\d+\b", "", text_value)
    text_value = re.sub(r"0\s*5\s*[012]\s*[12]", "", text_value)
    text_value = re.sub(r"CCC_05[012][12].*", "", text_value)
    return text_value


def strip_following_instruction_block(question_text: str) -> str:
    raw_instruction_patterns = [
        r"\n\s*àíZ H«\$\.\s*0?\d+\s+Vo\s+0?\d+\s+gmR>r\s+gyMZm\s*-.*",
        r"\n\s*प्रश्न क्र\.\s*[०0]?[१-९1-9]\d*\s+ते\s+[०0]?[१-९1-9]\d*\s+साठी\s+सूचना\s*-.*",
        r"\n\s*Question\s+No\.?\s*0?\d+\s+to\s+0?\d+.*",
        r"\n\s*SECTION\s*-\s*II.*",
        r"\n\s*विभाग\s*-\s*II.*",
    ]
    for pattern in raw_instruction_patterns:
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


def extract_page_text(page: fitz.Page, *, convert_legacy_marathi: bool = False) -> str:
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


def extract_questions(pdf_path: Path, *, convert_legacy_marathi: bool = False) -> dict[int, ExtractedQuestion]:
    doc = fitz.open(str(pdf_path))
    text_parts: list[str] = []
    page_text_by_index: dict[int, str] = {}
    for page_index, page in enumerate(doc):
        if page_index == 0:
            continue
        page_text = clean_pdf_text(extract_page_text(page, convert_legacy_marathi=convert_legacy_marathi))
        page_text_by_index[page_index] = page_text
        text_parts.append(page_text)

    full_text = "\n".join(text_parts)
    q_re = re.compile(
        r"(?:^|\n)\s*(?:0?([1-9]|[1-6][0-9]|7[0-5])|०?([१-९]|[१-६][०-९]|७[०-५]))\.\s+",
        re.M,
    )
    scan_text = "\n" + full_text
    matches = list(q_re.finditer(scan_text))
    questions: dict[int, ExtractedQuestion] = {}
    for idx, match in enumerate(matches):
        q_no = int(devanagari_digit_to_ascii(match.group(1) or match.group(2)))
        start = max(match.end() - 1, 0)
        end = matches[idx + 1].start() - 1 if idx + 1 < len(matches) else len(full_text)
        if not 1 <= q_no <= 75:
            continue
        body = normalize_text(full_text[start:end])
        stem, options = split_options(body)
        questions[q_no] = ExtractedQuestion(question_no=q_no, text=stem, options=options)

    locations = locate_question_regions(doc)
    for q_no, extracted in questions.items():
        if q_no in locations:
            extracted.page_index, extracted.crop = locations[q_no]
    return questions


def locate_question_regions(doc: fitz.Document) -> dict[int, tuple[int, tuple[float, float, float, float]]]:
    locations: dict[int, tuple[int, tuple[float, float, float, float]]] = {}
    for page_index, page in enumerate(doc):
        if page_index == 0:
            continue
        words = page.get_text("words")
        markers: list[tuple[int, float]] = []
        for word in words:
            x0, y0, _x1, _y1, token = word[:5]
            token = str(token).strip()
            matched = re.fullmatch(r"0?([1-9]|[1-6][0-9]|7[0-5])\.", token)
            if matched and x0 < page.rect.width * 0.25:
                markers.append((int(matched.group(1)), float(y0)))
        markers = sorted(set(markers), key=lambda item: item[1])
        for idx, (q_no, y0) in enumerate(markers):
            next_y = markers[idx + 1][1] if idx + 1 < len(markers) else min(y0 + 180, page.rect.height - 20)
            y1 = max(min(next_y - 4, page.rect.height - 20), y0 + 45)
            rect = (30.0, max(y0 - 8, 20.0), page.rect.width - 30.0, y1)
            locations[q_no] = (page_index, rect)
    return locations


async def fetch_db_questions(database_url: str) -> dict[int, dict[int, DbQuestion]]:
    engine = create_async_engine(database_url)
    output: dict[int, dict[int, DbQuestion]] = {}
    async with engine.connect() as conn:
        q_rows = (
            await conn.execute(
                text(
                    """
                    select id, exam_id, question_no, question_type, text_en, text_mr,
                           question_image_url
                    from questions
                    where exam_id in (16, 17)
                    order by exam_id, question_no
                    """
                )
            )
        ).mappings().all()
        question_ids = [row["id"] for row in q_rows]
        opt_rows = (
            await conn.execute(
                text(
                    """
                    select id, question_id, option_no, text_en, text_mr, image_url
                    from options
                    where question_id = any(:question_ids)
                    order by question_id, option_no
                    """
                ),
                {"question_ids": question_ids},
            )
        ).mappings().all()

    await engine.dispose()

    options_by_question: dict[int, list[DbOption]] = {}
    for row in opt_rows:
        options_by_question.setdefault(row["question_id"], []).append(
            DbOption(
                id=row["id"],
                option_no=row["option_no"],
                text_en=row["text_en"],
                text_mr=row["text_mr"],
                image_url=row["image_url"],
            )
        )

    for row in q_rows:
        q = DbQuestion(
            id=row["id"],
            exam_id=row["exam_id"],
            question_no=row["question_no"],
            question_type=row["question_type"],
            text_en=row["text_en"],
            text_mr=row["text_mr"],
            question_image_url=row["question_image_url"],
            options=options_by_question.get(row["id"], []),
        )
        output.setdefault(q.exam_id, {})[q.question_no] = q
    return output


def has_image_hint(*texts: str | None) -> bool:
    combined = " ".join(normalize_text(t).lower() for t in texts if t)
    return any(hint in combined for hint in IMAGE_HINTS_EN) or any(hint in combined for hint in IMAGE_HINTS_MR)


def similarity(a: str | None, b: str | None) -> float:
    a_norm = normalize_text(a).lower()
    b_norm = normalize_text(b).lower()
    if not a_norm or not b_norm:
        return 0.0
    a_tokens = set(re.findall(r"\w+", a_norm))
    b_tokens = set(re.findall(r"\w+", b_norm))
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / max(len(a_tokens | b_tokens), 1)


def status_for(db_q: DbQuestion, en_q: ExtractedQuestion | None, mr_q: ExtractedQuestion | None) -> tuple[str, list[str]]:
    warnings: list[str] = []
    en_text = en_q.text if en_q else ""
    mr_text = mr_q.text if mr_q else ""

    if en_q and db_q.text_en and similarity(db_q.text_en, en_text) < 0.25:
        warnings.append("Existing English text differs from PDF extraction")
    if mr_q and db_q.text_mr and similarity(db_q.text_mr, mr_text) < 0.25:
        warnings.append("Existing Marathi text differs from PDF extraction")
    if en_q and len(en_q.options) != 4:
        warnings.append(f"English extraction found {len(en_q.options)} options")
    if mr_q and len(mr_q.options) != 4:
        warnings.append(f"Marathi extraction found {len(mr_q.options)} options")
    if mr_q and (has_shree_dev_artifacts(mr_q.text) or any(has_shree_dev_artifacts(option) for option in mr_q.options)):
        warnings.append("Marathi extraction still contains legacy Shree Dev artifacts")
    if len(db_q.options) != 4:
        warnings.append(f"DB has {len(db_q.options)} options")

    if warnings:
        return "needs_review", warnings
    if en_q and mr_q:
        return "safe_merge", warnings
    if en_q or mr_q:
        return "language_specific", warnings
    return "needs_review", ["Question number not found in either PDF extraction"]


def proposed_type(db_q: DbQuestion, en_q: ExtractedQuestion | None, mr_q: ExtractedQuestion | None, needs_image: bool) -> str:
    has_en = bool(en_q and en_q.text) or bool(db_q.text_en)
    has_mr = bool(mr_q and mr_q.text) or bool(db_q.text_mr)
    if db_q.question_type == "image_only":
        return "image_only"
    if needs_image and has_en:
        return "text_image"
    if has_en and has_mr:
        return "bilingual"
    if has_mr and not has_en:
        return "marathi_only"
    return db_q.question_type or "text"


def blank_score(pix: fitz.Pixmap) -> float:
    samples = pix.samples
    if not samples:
        return 1.0
    step = max(pix.n, 1) * 16
    values = samples[0::step]
    if not values:
        return 1.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return 1.0 / (1.0 + variance)


def render_crop(pdf_path: Path, item: ManifestItem, output_dir: Path) -> None:
    if not item.needs_image or not item.crop_box or item.crop_page is None:
        return
    previews_dir = output_dir / "previews" / item.paper_code
    previews_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    page = doc[item.crop_page]
    rect = fitz.Rect(*item.crop_box)
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=rect, alpha=False)
    item.crop_blank_score = round(blank_score(pix), 5)
    rel_path = Path("previews") / item.paper_code / f"q{item.question_no:02d}.png"
    pix.save(str(output_dir / rel_path))
    item.crop_preview = rel_path.as_posix()


def build_manifest(test_dir: Path, db_questions: dict[int, dict[int, DbQuestion]], output_dir: Path) -> list[ManifestItem]:
    manifest: list[ManifestItem] = []
    for paper_code, cfg in EXAMS.items():
        exam_id = cfg["exam_id"]
        english_pdf = test_dir / cfg["english_pdf"]
        marathi_pdf = test_dir / cfg["marathi_pdf"]
        if not english_pdf.exists():
            raise FileNotFoundError(english_pdf)
        if not marathi_pdf.exists():
            raise FileNotFoundError(marathi_pdf)

        english_questions = extract_questions(english_pdf)
        marathi_questions = extract_questions(marathi_pdf, convert_legacy_marathi=True)

        for q_no in range(1, 76):
            db_q = db_questions.get(exam_id, {}).get(q_no)
            if not db_q:
                continue
            en_q = english_questions.get(q_no)
            mr_q = marathi_questions.get(q_no)
            status, warnings = status_for(db_q, en_q, mr_q)
            if any(start <= q_no <= end for start, end in DO_NOT_MERGE_LANGUAGE_SPECIFIC_RANGES.get(paper_code, [])):
                status = "needs_review"
                warnings.append("Language-specific section; English and Marathi PDFs are not the same question set")
            needs_image = (
                db_q.question_type == "image_only"
                or bool(db_q.question_image_url and "PLACEHOLDER" in db_q.question_image_url)
                or has_image_hint(db_q.text_en, db_q.text_mr, en_q.text if en_q else "", mr_q.text if mr_q else "")
            )
            if (paper_code, q_no) in MANUAL_NO_IMAGE:
                needs_image = False
            crop_source = en_q if en_q and en_q.crop else mr_q
            manual_crop = MANUAL_CROP_OVERRIDES.get((paper_code, q_no))
            item = ManifestItem(
                paper_code=paper_code,
                exam_id=exam_id,
                question_id=db_q.id,
                question_no=q_no,
                status=status,
                current_question_type=db_q.question_type,
                proposed_question_type=proposed_type(db_q, en_q, mr_q, needs_image),
                current_text_en=db_q.text_en,
                current_text_mr=db_q.text_mr,
                extracted_text_en=en_q.text if en_q else None,
                extracted_text_mr=mr_q.text if mr_q else None,
                extracted_options_en=en_q.options if en_q else [],
                extracted_options_mr=mr_q.options if mr_q else [],
                needs_image=needs_image,
                crop_page=manual_crop[0] if manual_crop else (crop_source.page_index if crop_source else None),
                crop_box=list(manual_crop[1]) if manual_crop else (list(crop_source.crop) if crop_source and crop_source.crop else None),
                crop_preview=None,
                crop_blank_score=None,
                warnings=warnings,
            )
            if needs_image:
                render_crop(english_pdf if en_q and en_q.crop else marathi_pdf, item, output_dir)
            item.option_updates = option_update_preview(db_q, en_q, mr_q)
            manifest.append(item)
    return manifest


def option_update_preview(
    db_q: DbQuestion, en_q: ExtractedQuestion | None, mr_q: ExtractedQuestion | None
) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for idx, db_opt in enumerate(sorted(db_q.options, key=lambda o: o.option_no)):
        updates.append(
            {
                "option_id": db_opt.id,
                "option_no": db_opt.option_no,
                "current_text_en": db_opt.text_en,
                "current_text_mr": db_opt.text_mr,
                "extracted_text_en": en_q.options[idx] if en_q and len(en_q.options) > idx else None,
                "extracted_text_mr": mr_q.options[idx] if mr_q and len(mr_q.options) > idx else None,
            }
        )
    return updates


def write_outputs(manifest: list[ManifestItem], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_dicts = [asdict(item) for item in manifest]
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest_dicts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (output_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "paper_code",
                "exam_id",
                "question_id",
                "question_no",
                "status",
                "current_question_type",
                "proposed_question_type",
                "needs_image",
                "crop_page",
                "crop_preview",
                "crop_blank_score",
                "warnings",
            ],
        )
        writer.writeheader()
        for item in manifest:
            writer.writerow(
                {
                    "paper_code": item.paper_code,
                    "exam_id": item.exam_id,
                    "question_id": item.question_id,
                    "question_no": item.question_no,
                    "status": item.status,
                    "current_question_type": item.current_question_type,
                    "proposed_question_type": item.proposed_question_type,
                    "needs_image": item.needs_image,
                    "crop_page": item.crop_page,
                    "crop_preview": item.crop_preview,
                    "crop_blank_score": item.crop_blank_score,
                    "warnings": "; ".join(item.warnings),
                }
            )
    (output_dir / "qa_report.html").write_text(render_html(manifest), encoding="utf-8")


def render_html(manifest: list[ManifestItem]) -> str:
    rows = []
    for item in manifest:
        preview = ""
        if item.crop_preview:
            preview = f'<img src="{html.escape(item.crop_preview)}" alt="Q{item.question_no} crop">'
        warnings = "<br>".join(html.escape(w) for w in item.warnings)
        rows.append(
            f"""
            <tr class="{html.escape(item.status)}">
              <td>{html.escape(item.paper_code)}</td>
              <td>{item.question_no}</td>
              <td>{html.escape(item.status)}</td>
              <td>{html.escape(item.current_question_type)} -> {html.escape(item.proposed_question_type)}</td>
              <td>{html.escape((item.extracted_text_en or '')[:500])}</td>
              <td>{html.escape((item.extracted_text_mr or '')[:500])}</td>
              <td>{preview}</td>
              <td>{warnings}</td>
            </tr>
            """
        )
    summary = summarize(manifest)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>MSCE 2022 Std 5 Backfill QA</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 24px; color: #111827; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; vertical-align: top; font-size: 13px; }}
    th {{ background: #f3f4f6; position: sticky; top: 0; }}
    img {{ max-width: 360px; max-height: 260px; border: 1px solid #e5e7eb; }}
    .needs_review {{ background: #fff7ed; }}
    .safe_merge {{ background: #f0fdf4; }}
    .language_specific {{ background: #eff6ff; }}
    pre {{ background: #f9fafb; padding: 12px; border: 1px solid #e5e7eb; }}
  </style>
</head>
<body>
  <h1>MSCE 2022 Std 5 Backfill QA</h1>
  <pre>{html.escape(json.dumps(summary, ensure_ascii=False, indent=2))}</pre>
  <table>
    <thead>
      <tr>
        <th>Paper</th><th>Q</th><th>Status</th><th>Type</th>
        <th>English Extract</th><th>Marathi Extract</th><th>Crop</th><th>Warnings</th>
      </tr>
    </thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""


def summarize(manifest: list[ManifestItem]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total": len(manifest),
        "by_status": {},
        "needs_image": sum(1 for item in manifest if item.needs_image),
        "with_crop": sum(1 for item in manifest if item.crop_preview),
        "by_paper": {},
    }
    for item in manifest:
        summary["by_status"][item.status] = summary["by_status"].get(item.status, 0) + 1
        paper = summary["by_paper"].setdefault(item.paper_code, {"total": 0, "needs_image": 0, "needs_review": 0})
        paper["total"] += 1
        paper["needs_image"] += int(item.needs_image)
        paper["needs_review"] += int(item.status == "needs_review")
    return summary


def filter_manifest(manifest: list[ManifestItem], args: argparse.Namespace) -> list[ManifestItem]:
    filtered = manifest
    if args.paper_code:
        filtered = [item for item in filtered if item.paper_code == args.paper_code]
    if args.question_from is not None:
        filtered = [item for item in filtered if item.question_no >= args.question_from]
    if args.question_to is not None:
        filtered = [item for item in filtered if item.question_no <= args.question_to]
    return filtered


async def upload_to_r2(env: dict[str, str], file_path: Path, key: str) -> str:
    required = ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME", "R2_PUBLIC_URL"]
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise RuntimeError(f"Missing R2 settings: {', '.join(missing)}")
    session = aioboto3.Session(
        aws_access_key_id=env["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    endpoint = f"https://{env['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    async with session.client("s3", endpoint_url=endpoint) as s3:
        await s3.put_object(
            Bucket=env["R2_BUCKET_NAME"],
            Key=key,
            Body=file_path.read_bytes(),
            ContentType="image/png",
        )
    return f"{env['R2_PUBLIC_URL'].rstrip('/')}/{key}"


async def apply_updates(args: argparse.Namespace, env: dict[str, str], manifest: list[ManifestItem], output_dir: Path) -> None:
    if not args.apply_text and not args.apply_images:
        return
    if args.require_clean_review and any(item.status == "needs_review" for item in manifest):
        raise RuntimeError("Manifest contains needs_review rows; rerun without --require-clean-review to override")

    engine = create_async_engine(db_url(env))
    async with engine.begin() as conn:
        has_media_files = bool(
            (
                await conn.execute(
                    text("select to_regclass('public.media_files') is not null")
                )
            ).scalar()
        )
        for item in manifest:
            if item.status == "needs_review" and not args.apply_needs_review:
                continue

            if args.apply_text:
                await conn.execute(
                    text(
                        """
                        update questions
                        set text_en = coalesce(:text_en, text_en),
                            text_mr = coalesce(:text_mr, text_mr),
                            question_type = :question_type
                        where id = :question_id
                        """
                    ),
                    {
                        "question_id": item.question_id,
                        "text_en": item.extracted_text_en,
                        "text_mr": item.extracted_text_mr,
                        "question_type": item.proposed_question_type,
                    },
                )
                for opt in item.option_updates:
                    await conn.execute(
                        text(
                            """
                            update options
                            set text_en = coalesce(:text_en, text_en),
                                text_mr = coalesce(:text_mr, text_mr)
                            where id = :option_id
                            """
                        ),
                        {
                            "option_id": opt["option_id"],
                            "text_en": opt["extracted_text_en"],
                            "text_mr": opt["extracted_text_mr"],
                        },
                    )

            if args.apply_images and item.crop_preview:
                preview_path = output_dir / item.crop_preview
                key = f"exams/{item.exam_id}/questions/{item.question_id}/q{item.question_no:02d}-{uuid4().hex}.png"
                public_url = await upload_to_r2(env, preview_path, key)
                await conn.execute(
                    text("update questions set question_image_url = :url where id = :question_id"),
                    {"url": public_url, "question_id": item.question_id},
                )
                if has_media_files:
                    await conn.execute(
                        text(
                            """
                            insert into media_files
                              (file_type, original_filename, storage_key, file_url, content_type, file_size)
                            values
                              ('question', :filename, :key, :url, 'image/png', :file_size)
                            """
                        ),
                        {
                            "filename": preview_path.name,
                            "key": key,
                            "url": public_url,
                            "file_size": preview_path.stat().st_size,
                        },
                    )
    await engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-dir", type=Path, default=DEFAULT_TEST_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--apply-text", action="store_true", help="Update extracted text/type fields in Supabase")
    parser.add_argument("--apply-images", action="store_true", help="Upload rendered crops to R2 and update question_image_url")
    parser.add_argument("--apply-needs-review", action="store_true", help="Also apply rows marked needs_review")
    parser.add_argument("--require-clean-review", action="store_true", help="Abort apply if any row is marked needs_review")
    parser.add_argument("--paper-code", choices=sorted(EXAMS), help="Limit output/apply to one paper code")
    parser.add_argument("--question-from", type=int, help="Limit output/apply to questions at or after this number")
    parser.add_argument("--question-to", type=int, help="Limit output/apply to questions at or before this number")
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    env = load_env()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    db_questions = await fetch_db_questions(db_url(env))
    manifest = build_manifest(args.test_dir, db_questions, args.output_dir)
    manifest = filter_manifest(manifest, args)
    write_outputs(manifest, args.output_dir)
    await apply_updates(args, env, manifest, args.output_dir)

    summary = summarize(manifest)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Manifest: {args.output_dir / 'manifest.json'}")
    print(f"QA report: {args.output_dir / 'qa_report.html'}")
    if args.apply_text or args.apply_images:
        print("Applied requested updates.")
    else:
        print("Review-only run complete. No DB updates or R2 uploads were performed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
