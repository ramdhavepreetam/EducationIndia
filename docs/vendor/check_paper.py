#!/usr/bin/env python3
"""
ScholarPath — question paper delivery checker.

Validates a vendor-produced paper JSON against QUESTION_PAPER_SPEC.md.
Pure standard library: no database, no ScholarPath code, no dependencies.
Vendors can run this themselves before delivering.

Usage:
    python3 check_paper.py mypaper.json
    python3 check_paper.py mypaper.json --images ./images   # verify image files exist
    python3 check_paper.py mypaper.json --strict            # require all 75 questions

Exit code 0 = valid, 1 = errors found.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

QUESTION_TYPES = {
    "text",
    "text_image",
    "image_only",
    "context_text",
    "context_image",
    "marathi_only",
    "bilingual",
}
DIFFICULTIES = {"easy", "medium", "hard"}
# MSCE runs PUP (currently Std 5, moving to Std 4) and PSS (Std 8, moving to Std 7).
# paper_code is <std><paper number>: 501 = Std 5 Paper I, 802 = Std 8 Paper II.
STD_CLASSES = {4, 5, 7, 8}
PAPER_CODES = {f"{s}{p}" for s in STD_CLASSES for p in ("01", "02")}
CONTEXT_TYPES = {
    "paragraph", "poem", "advertisement", "image", "pictograph",
    "instruction", "venn_diagram", "figure_series", "table", "data_chart",
}
TOPICS = {
    "English": {
        "Reading Comprehension", "Poetry", "Advertisement Reading",
        "Grammar", "Vocabulary", "Picture Comprehension",
    },
    "Mathematics": {
        "Weights and Measures", "Fractions", "Profit and Loss",
        "Simple Interest", "Geometry", "Percentages", "Time and Distance",
        "Number System", "Data Handling", "Algebra", "Calendar and Clock",
    },
    "Marathi": {
        "Vocabulary", "Grammar", "Reading Comprehension", "Poetry",
        "Idioms and Proverbs",
    },
    "Intelligence Test": {
        "Mirror and Water Images", "Analogy", "Series Completion",
        "Pattern Recognition", "Direction and Position", "Coding and Decoding",
        "Venn Diagrams", "Number Puzzles", "Odd One Out", "Logic and Reasoning",
    },
}
SECTION_RANGE = {
    "English": (1, 25), "Marathi": (1, 25),
    "Mathematics": (26, 75), "Intelligence Test": (26, 75),
}

# Legacy Marathi font encodings produce Latin letters where Devanagari belongs.
# A "Marathi" string with no Devanagari at all is almost always Shree Dev / Kruti Dev.
DEVANAGARI = range(0x0900, 0x0980)


def has_devanagari(text: str) -> bool:
    return any(ord(ch) in DEVANAGARI for ch in text)


def content_of(item: dict, *keys: str) -> bool:
    """True when at least one of the named fields holds real content."""
    return any((item.get(k) or "").strip() if isinstance(item.get(k), str) else item.get(k) for k in keys)


def check(path: Path, images_dir: Path | None, strict: bool) -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"File is not valid UTF-8: {exc}"]
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}"]

    if not isinstance(doc, dict):
        return ["Top level must be a JSON object"]

    questions = doc.get("questions")
    contexts = doc.get("contexts", [])
    if not isinstance(questions, list) or not questions:
        return ["'questions' must be a non-empty array"]
    if not isinstance(contexts, list):
        return ["'contexts' must be an array"]

    # ── paper block ──────────────────────────────────────────────────────────
    paper = doc.get("paper")
    if not isinstance(paper, dict):
        errors.append("Missing 'paper' object")
    else:
        std = paper.get("std_class")
        code = paper.get("paper_code")
        if std not in STD_CLASSES:
            errors.append(f"paper.std_class must be one of {sorted(STD_CLASSES)}, got {std!r}")
        if code not in PAPER_CODES:
            errors.append(
                f"paper.paper_code must be one of {sorted(PAPER_CODES)}, got {code!r}. "
                "The first digit is the standard, the last is the paper number "
                "(e.g. 801 = Std 8 Paper I)."
            )
        elif std in STD_CLASSES and not code.startswith(str(std)):
            errors.append(
                f"paper.paper_code {code!r} does not match std_class {std} — "
                f"expected {std}01 or {std}02"
            )

    # ── contexts ─────────────────────────────────────────────────────────────
    for idx, ctx in enumerate(contexts):
        if ctx.get("context_type") not in CONTEXT_TYPES:
            errors.append(f"contexts[{idx}]: context_type {ctx.get('context_type')!r} is not allowed")
        if not content_of(ctx, "content_en", "content_mr", "image"):
            errors.append(f"contexts[{idx}]: has no content_en, content_mr or image")

    # ── questions ────────────────────────────────────────────────────────────
    seen: dict[int, int] = {}
    referenced_images: set[str] = set()

    for pos, q in enumerate(questions):
        no = q.get("question_no")
        p = f"Q{no}" if no is not None else f"questions[{pos}]"

        if not isinstance(no, int) or not 1 <= no <= 75:
            errors.append(f"{p}: question_no must be an integer 1-75")
            continue
        if no in seen:
            errors.append(f"{p}: duplicate question_no (also at questions[{seen[no]}])")
        seen[no] = pos

        section = q.get("section")
        if section not in TOPICS:
            errors.append(f"{p}: section {section!r} must be one of {sorted(TOPICS)}")
        else:
            lo, hi = SECTION_RANGE[section]
            if not lo <= no <= hi:
                errors.append(f"{p}: question_no {no} is outside {section} range {lo}-{hi}")
            if q.get("topic") not in TOPICS[section]:
                errors.append(
                    f"{p}: topic {q.get('topic')!r} is not valid for {section}. "
                    f"Allowed: {sorted(TOPICS[section])}"
                )

        qtype = q.get("question_type")
        if qtype not in QUESTION_TYPES:
            errors.append(f"{p}: question_type {qtype!r} is not one of {sorted(QUESTION_TYPES)}")
            continue
        if q.get("difficulty") not in DIFFICULTIES:
            errors.append(f"{p}: difficulty must be easy/medium/hard, got {q.get('difficulty')!r}")

        cancelled = bool(q.get("is_cancelled", False))
        multi = bool(q.get("is_multi_select", False))
        correct = q.get("correct_option")
        correct_many = q.get("correct_options")
        if cancelled:
            if correct is not None or correct_many:
                errors.append(f"{p}: cancelled question must have correct_option and correct_options null")
            if not (q.get("cancelled_reason") or "").strip():
                warnings.append(f"{p}: cancelled without a cancelled_reason")
        elif multi:
            # "choose two" style question: correct_options carries the answers
            if correct is not None:
                errors.append(f"{p}: multi-select question must have correct_option null "
                              "(use correct_options instead)")
            if not isinstance(correct_many, list) or not correct_many:
                errors.append(f"{p}: multi-select question requires a non-empty correct_options array")
            else:
                bad = [v for v in correct_many if v not in (1, 2, 3, 4)]
                if bad:
                    errors.append(f"{p}: correct_options values must be 1-4, got {bad}")
                if len(set(correct_many)) != len(correct_many):
                    errors.append(f"{p}: correct_options must not contain duplicates")
                if len(set(correct_many)) < 2:
                    errors.append(f"{p}: multi-select needs at least 2 correct_options, got {correct_many}")
                if len(set(correct_many)) == 4:
                    errors.append(f"{p}: all four options marked correct — that is not a valid question")
        else:
            if correct not in (1, 2, 3, 4):
                errors.append(f"{p}: correct_option must be 1-4, got {correct!r}")
            if correct_many:
                errors.append(f"{p}: correct_options is set but is_multi_select is not true")

        ref = q.get("context_ref")
        if ref is not None and not (isinstance(ref, int) and 0 <= ref < len(contexts)):
            errors.append(f"{p}: context_ref {ref!r} is out of range (contexts has {len(contexts)})")

        options = q.get("options")
        if not isinstance(options, list) or len(options) != 4:
            errors.append(f"{p}: exactly 4 options required, got {len(options) if isinstance(options, list) else 'none'}")
            continue
        if sorted(o.get("option_no") for o in options) != [1, 2, 3, 4]:
            errors.append(f"{p}: option_no values must be exactly 1,2,3,4")

        # every option must show the student something
        for o in options:
            if not content_of(o, "text_en", "text_mr", "image"):
                errors.append(
                    f"{p}: option {o.get('option_no')} is BLANK — needs text or an image"
                )

        # the correct answer specifically must not be blank
        if not cancelled:
            answer_nos = []
            if multi and isinstance(correct_many, list):
                answer_nos = [v for v in correct_many if v in (1, 2, 3, 4)]
            elif correct in (1, 2, 3, 4):
                answer_nos = [correct]
            for ans in answer_nos:
                chosen = next((o for o in options if o.get("option_no") == ans), None)
                if chosen and not content_of(chosen, "text_en", "text_mr", "image"):
                    errors.append(
                        f"{p}: CORRECT ANSWER (option {ans}) IS BLANK — "
                        "students cannot answer this question correctly"
                    )

        # ── type-specific rules ──────────────────────────────────────────────
        stem_img = q.get("question_image")
        if qtype == "text":
            if not (q.get("text_en") or "").strip():
                errors.append(f"{p}: type 'text' requires text_en")
            for o in options:
                if not (o.get("text_en") or "").strip():
                    errors.append(f"{p}: option {o.get('option_no')} requires text_en for type 'text'")
        elif qtype == "text_image":
            if not content_of(q, "text_en", "text_mr"):
                errors.append(f"{p}: type 'text_image' requires text_en or text_mr")
            if not stem_img:
                errors.append(f"{p}: type 'text_image' requires question_image")
        elif qtype == "image_only":
            if q.get("text_en") is not None or q.get("text_mr") is not None:
                errors.append(f"{p}: type 'image_only' must have text_en and text_mr set to null")
            if not stem_img and ref is None:
                errors.append(f"{p}: type 'image_only' requires question_image or context_ref")
            for o in options:
                if not o.get("image"):
                    errors.append(f"{p}: option {o.get('option_no')} requires an image for type 'image_only'")
        elif qtype == "context_text":
            if ref is None:
                errors.append(f"{p}: type 'context_text' requires context_ref")
            if not content_of(q, "text_en", "text_mr"):
                errors.append(f"{p}: type 'context_text' requires text_en or text_mr")
        elif qtype == "context_image":
            if ref is None:
                errors.append(f"{p}: type 'context_image' requires context_ref")
            for o in options:
                if not o.get("image"):
                    errors.append(f"{p}: option {o.get('option_no')} requires an image for type 'context_image'")
        elif qtype == "marathi_only":
            if not (q.get("text_mr") or "").strip():
                errors.append(f"{p}: type 'marathi_only' requires text_mr")
            if q.get("text_en") is not None:
                errors.append(f"{p}: type 'marathi_only' must have text_en set to null")
            for o in options:
                if not (o.get("text_mr") or "").strip():
                    errors.append(f"{p}: option {o.get('option_no')} requires text_mr for type 'marathi_only'")
        elif qtype == "bilingual":
            if not (q.get("text_en") or "").strip():
                errors.append(f"{p}: type 'bilingual' requires text_en")
            if not (q.get("text_mr") or "").strip():
                errors.append(f"{p}: type 'bilingual' requires text_mr")

        # ── legacy Marathi font detection ────────────────────────────────────
        mr_fields = [q.get("text_mr") or ""] + [o.get("text_mr") or "" for o in options]
        for value in mr_fields:
            stripped = value.strip()
            if stripped and not has_devanagari(stripped) and any(c.isalpha() for c in stripped):
                warnings.append(
                    f"{p}: Marathi field has no Devanagari characters ({stripped[:30]!r}) — "
                    "possible legacy Shree Dev / Kruti Dev encoding"
                )
                break

        # ── image bookkeeping ────────────────────────────────────────────────
        if stem_img:
            referenced_images.add(stem_img)
            if not content_of(q, "question_image_alt_en", "question_image_alt_mr"):
                warnings.append(f"{p}: question_image has no alt text")
        for o in options:
            if o.get("image"):
                referenced_images.add(o["image"])
                if not content_of(o, "image_alt_en", "image_alt_mr"):
                    warnings.append(f"{p}: option {o.get('option_no')} image has no alt text")

    for ctx in contexts:
        if ctx.get("image"):
            referenced_images.add(ctx["image"])

    # ── whole-paper checks ───────────────────────────────────────────────────
    if strict:
        missing = sorted(set(range(1, 76)) - set(seen))
        if missing:
            errors.append(f"Paper is incomplete — missing question numbers: {missing}")

    if images_dir:
        for name in sorted(referenced_images):
            if not (images_dir / name).exists():
                errors.append(f"Image file not found in {images_dir}: {name}")

    # ── report ───────────────────────────────────────────────────────────────
    print(f"File      : {path}")
    if isinstance(paper, dict):
        print(f"Paper     : {paper.get('paper_code')} set {paper.get('set_code')} · "
              f"std {paper.get('std_class')} · {paper.get('year')} · {paper.get('medium')}")
    print(f"Questions : {len(questions)}")
    print(f"Contexts  : {len(contexts)}")
    print(f"Types     : {dict(Counter(q.get('question_type') for q in questions))}")

    diff = Counter(q.get("difficulty") for q in questions)
    total = sum(diff.values()) or 1
    print(f"Difficulty: {dict(diff)}  "
          f"({100*diff['easy']//total}% easy / {100*diff['medium']//total}% medium / "
          f"{100*diff['hard']//total}% hard, target 40/40/20)")
    if diff["medium"] / total > 0.75:
        warnings.append(
            "Over 75% of questions are 'medium' — difficulty looks unlabelled. "
            "This prevents blueprint-weighted practice papers."
        )
    print(f"Images    : {len(referenced_images)} referenced"
          + (f", checked against {images_dir}" if images_dir else " (not checked — pass --images DIR)"))
    print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings[:40]:
            print(f"  ! {w}")
        if len(warnings) > 40:
            print(f"  ... and {len(warnings)-40} more")
        print()

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--images", type=Path, default=None, help="folder holding the image files")
    ap.add_argument("--strict", action="store_true", help="require all 75 questions to be present")
    args = ap.parse_args()

    if not args.file.exists():
        print(f"File not found: {args.file}")
        return 1

    errors = check(args.file, args.images, args.strict)
    if errors:
        print(f"REJECTED — {len(errors)} error(s):\n")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("ACCEPTED — paper is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
