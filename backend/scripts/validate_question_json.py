#!/usr/bin/env python3
"""
Validate a bulk question-import JSON file BEFORE sending it to the API.

Runs the same validator the import endpoint uses (importer.validate_question_import)
plus file-level checks the per-question validator cannot see: duplicate question
numbers, dangling context_ref indexes, and the DB CHECK constraints added on
2026-08-17.

Usage:
    PYTHONPATH=backend backend/.venv/bin/python \\
        backend/scripts/validate_question_json.py docs/question-import-template.json

    # also verify section_id/topic_id/question_no against the live database:
    ... validate_question_json.py myfile.json --check-db

Exit code 0 = valid, 1 = errors found.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.modules.question.importer import validate_question_import  # noqa: E402
from app.modules.question.schemas import BulkImportSchema  # noqa: E402

VALID_TYPES = {
    "text",
    "text_image",
    "image_only",
    "context_text",
    "context_image",
    "marathi_only",
    "bilingual",
}
VALID_DIFFICULTY = {"easy", "medium", "hard"}
VALID_CONTEXT_TYPES = {
    "paragraph",
    "poem",
    "advertisement",
    "image",
    "pictograph",
    "instruction",
    "venn_diagram",
    "figure_series",
    "table",
    "data_chart",
}


def _strip_comments(node):
    """Remove _comment/_README keys so authoring notes never reach the parser."""
    if isinstance(node, dict):
        return {k: _strip_comments(v) for k, v in node.items() if not k.startswith("_")}
    if isinstance(node, list):
        return [_strip_comments(item) for item in node]
    return node


def _option_has_content(opt) -> bool:
    return bool(
        (opt.text_en or "").strip()
        or (opt.text_mr or "").strip()
        or opt.image_url
    )


def validate_file(path: Path) -> tuple[list[str], BulkImportSchema | None]:
    errors: list[str] = []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON: line {exc.lineno} col {exc.colno}: {exc.msg}"], None

    try:
        payload = BulkImportSchema.model_validate(_strip_comments(raw))
    except Exception as exc:
        return [f"Schema error: {exc}"], None

    # ── file-level checks ────────────────────────────────────────────────────
    seen: dict[int, int] = {}
    for idx, q in enumerate(payload.questions):
        if q.question_no in seen:
            errors.append(
                f"Q{q.question_no}: duplicate question_no "
                f"(questions[{seen[q.question_no]}] and questions[{idx}])"
            )
        seen[q.question_no] = idx

    for idx, ctx in enumerate(payload.contexts):
        if ctx.context_type not in VALID_CONTEXT_TYPES:
            errors.append(
                f"contexts[{idx}]: unknown context_type '{ctx.context_type}'. "
                f"Valid: {', '.join(sorted(VALID_CONTEXT_TYPES))}"
            )

    # ── per-question checks ──────────────────────────────────────────────────
    for q in payload.questions:
        prefix = f"Q{q.question_no}"

        # the real importer's rules
        errors.extend(validate_question_import(q))

        if q.question_type not in VALID_TYPES:
            errors.append(f"{prefix}: unknown question_type '{q.question_type}'")
        if q.difficulty not in VALID_DIFFICULTY:
            errors.append(
                f"{prefix}: difficulty must be one of {sorted(VALID_DIFFICULTY)}, "
                f"got '{q.difficulty}'"
            )
        if q.context_ref is not None and not (0 <= q.context_ref < len(payload.contexts)):
            errors.append(
                f"{prefix}: context_ref {q.context_ref} is out of range "
                f"(contexts has {len(payload.contexts)} entries)"
            )
        if q.marks <= 0:
            errors.append(f"{prefix}: marks must be positive, got {q.marks}")

        # DB CHECK constraints (added 2026-08-17) — fail here, not at insert
        # context-bound questions draw their stem from the shared context row
        if not q.is_cancelled and q.context_ref is None:
            has_stem = bool(
                (q.text_en or "").strip()
                or (q.text_mr or "").strip()
                or q.question_image_url
            )
            if not has_stem:
                errors.append(
                    f"{prefix}: violates questions_stem_present_chk — "
                    "needs stem text or a stem image"
                )
            if q.question_type in {"image_only", "text_image"} and not q.question_image_url:
                errors.append(
                    f"{prefix}: violates questions_image_type_has_image_chk — "
                    f"'{q.question_type}' requires question_image_url"
                )

        for opt in q.options:
            if not _option_has_content(opt):
                errors.append(
                    f"{prefix}: option {opt.option_no} violates "
                    "options_content_present_chk — needs text or an image. "
                    "(This is the defect that made 375 questions unanswerable.)"
                )

    return errors, payload


async def check_against_db(payload: BulkImportSchema) -> list[str]:
    """Verify exam/section/topic ids exist and question numbers are free."""
    import asyncpg

    env = REPO_ROOT / ".env"
    url = next(
        (
            line.split("=", 1)[1].strip()
            for line in env.read_text().splitlines()
            if line.startswith("DATABASE_URL=")
        ),
        None,
    )
    if not url:
        return ["--check-db: DATABASE_URL not found in .env"]

    conn = await asyncpg.connect(
        url.replace("postgresql+asyncpg://", "postgresql://"), statement_cache_size=0
    )
    try:
        errors: list[str] = []
        exam = await conn.fetchrow(
            "SELECT id, paper_code, is_active FROM exams WHERE id=$1", payload.exam_id
        )
        if exam is None:
            return [f"exam_id {payload.exam_id} does not exist"]

        valid_sections = {
            r["id"]: (r["question_from"], r["question_to"])
            for r in await conn.fetch(
                "SELECT id, question_from, question_to FROM sections WHERE exam_id=$1",
                payload.exam_id,
            )
        }
        valid_topics = {
            r["id"]: r["section_id"]
            for r in await conn.fetch(
                "SELECT t.id, t.section_id FROM topics t "
                "JOIN sections s ON s.id=t.section_id WHERE s.exam_id=$1",
                payload.exam_id,
            )
        }
        taken = {
            r["question_no"]
            for r in await conn.fetch(
                "SELECT question_no FROM questions WHERE exam_id=$1", payload.exam_id
            )
        }

        for q in payload.questions:
            prefix = f"Q{q.question_no}"
            if q.section_id not in valid_sections:
                errors.append(
                    f"{prefix}: section_id {q.section_id} does not belong to exam "
                    f"{payload.exam_id}. Valid: {sorted(valid_sections)}"
                )
            else:
                lo, hi = valid_sections[q.section_id]
                if not lo <= q.question_no <= hi:
                    errors.append(
                        f"{prefix}: question_no outside section range {lo}-{hi}"
                    )
            if q.topic_id not in valid_topics:
                errors.append(
                    f"{prefix}: topic_id {q.topic_id} does not belong to exam "
                    f"{payload.exam_id}"
                )
            elif q.section_id in valid_sections and valid_topics[q.topic_id] != q.section_id:
                errors.append(
                    f"{prefix}: topic_id {q.topic_id} belongs to section "
                    f"{valid_topics[q.topic_id]}, not {q.section_id}"
                )
            if q.question_no in taken:
                errors.append(
                    f"{prefix}: question_no already exists in exam {payload.exam_id} "
                    "(UNIQUE(exam_id, question_no) would reject this)"
                )
        return errors
    finally:
        await conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument(
        "--check-db",
        action="store_true",
        help="also verify ids and question numbers against the live database",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"File not found: {args.file}")
        return 1

    errors, payload = validate_file(args.file)

    if payload is not None and args.check_db and not errors:
        errors.extend(asyncio.run(check_against_db(payload)))

    if payload is not None:
        by_type: dict[str, int] = {}
        for q in payload.questions:
            by_type[q.question_type] = by_type.get(q.question_type, 0) + 1
        print(f"File     : {args.file}")
        print(f"exam_id  : {payload.exam_id}")
        print(f"contexts : {len(payload.contexts)}")
        print(f"questions: {len(payload.questions)}")
        for qtype, count in sorted(by_type.items()):
            print(f"   {qtype:<15} {count}")
        cancelled = sum(1 for q in payload.questions if q.is_cancelled)
        multi = sum(1 for q in payload.questions if q.is_multi_select)
        if cancelled:
            print(f"   (cancelled: {cancelled})")
        if multi:
            print(f"   (multi-select: {multi})")
        print()

    if errors:
        print(f"INVALID — {len(errors)} error(s):\n")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("VALID — safe to import.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
