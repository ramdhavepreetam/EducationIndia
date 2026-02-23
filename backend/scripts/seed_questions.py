"""
Seed script — imports MSCE 2025 exam questions into the database.

Reads two JSON files in BulkImportSchema format and calls the question
service's bulk_import() directly (no HTTP server needed).

Usage (from project root):
    DEBUG=true PYTHONPATH=backend python backend/scripts/seed_questions.py

Usage (from backend/ directory):
    DEBUG=true PYTHONPATH=. python scripts/seed_questions.py
"""

import asyncio
import json
import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
# Script lives at backend/scripts/seed_questions.py.
# Data files live at backend/data/msce_2025_paper_*.json.
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"

SEED_FILES = [
    DATA_DIR / "msce_2025_paper_501.json",
    DATA_DIR / "msce_2025_paper_502.json",
]

# ── Imports (after sys.path is set by PYTHONPATH) ─────────────────────────────
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.database import engine  # noqa: E402
from app.modules.question.schemas import BulkImportSchema  # noqa: E402
from app.modules.question.service import question_service  # noqa: E402
from app.shared.exceptions import BadRequest, NotFound  # noqa: E402


# ── Seed function ─────────────────────────────────────────────────────────────

async def seed_paper(db: AsyncSession, json_path: Path) -> None:
    """Load one JSON file and call bulk_import. Prints summary or exits on error."""
    print(f"\n[seed] Loading {json_path.name} ...")

    if not json_path.exists():
        print(f"[ERROR] File not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    raw = json_path.read_text(encoding="utf-8")
    try:
        data = BulkImportSchema(**json.loads(raw))
    except Exception as exc:
        print(f"[ERROR] JSON parse / schema validation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(
        f"[seed] exam_id={data.exam_id}  "
        f"contexts={len(data.contexts)}  "
        f"questions={len(data.questions)}"
    )

    try:
        result = await question_service.bulk_import(db, data)
    except NotFound as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except BadRequest as exc:
        print(f"[ERROR] Validation failed:\n  {exc}", file=sys.stderr)
        sys.exit(1)

    paper_label = f"Paper {data.exam_id}"
    print(
        f"[seed] {paper_label}: "
        f"{result.inserted} questions inserted, "
        f"{result.skipped} skipped"
    )
    if result.errors:
        print(f"[WARN] {len(result.errors)} import error(s):")
        for err in result.errors:
            print(f"  - {err}")


async def main() -> None:
    print("[seed] Starting MSCE 2025 question seeding ...")

    async with AsyncSession(engine, expire_on_commit=False) as db:
        async with db.begin():
            for path in SEED_FILES:
                await seed_paper(db, path)

    await engine.dispose()

    print("\n[seed] Done. Verify with:")
    print("  SELECT COUNT(*) FROM questions;          -- expect 150")
    print("  SELECT COUNT(*) FROM options;            -- expect 600")
    print("  SELECT COUNT(*) FROM question_contexts;  -- expect >= 11")
    print("  GET /api/questions/?exam_id=1            -- expect 75 items, no correct_option")
    print("  GET /api/questions/?exam_id=2            -- expect 75 items, no correct_option")


if __name__ == "__main__":
    asyncio.run(main())
