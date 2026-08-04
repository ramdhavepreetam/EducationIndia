#!/usr/bin/env python3
"""
Extract image_only question figures from Feb_2025/5th/English_Paper2.pdf
(exam_id=2, 2025 Std 5 Paper II — Intelligence Test).

Crops each question region, uploads to Cloudflare R2, updates question_image_url in DB.
Run from project root:
    python3 extract_upload_images_2025_5th_p2.py
"""

import asyncio
import sys
import os

sys.path.insert(0, "backend")

import fitz  # PyMuPDF
import boto3

PDF_PATH = "/Users/preetam/Desktop/Exam_Papers/Question_Papers/Feb_2025/5th/English_Paper2.pdf"
EXAM_ID = 2
ZOOM = 2.0  # 144 dpi — clear for Intelligence Test figures

# (page_0indexed, x0, y0, x1, y1) in PDF points (578×792 page)
# Verified by visual inspection of rendered pages
QUESTION_CROPS = {
    26: (6,  52,  55,  530, 320),   # dice net + 4 dice answer figures
    27: (6,  52, 318,  530, 468),   # 295 mirror image
    28: (6,  52, 464,  530, 592),   # CRY mirror image
    29: (7,  52,  44,  530, 202),   # L/△ water image
    30: (7,  52, 200,  530, 312),   # 671 water image
    31: (7,  52, 308,  530, 433),   # analogy (arrows/shapes)
    32: (7,  52, 430,  530, 592),   # arrow/shape analogy figures
    34: (8,  52, 222,  530, 270),   # 11:110::13:? (number analogy — text)
    36: (8,  52, 330,  530, 476),   # identical figure (vase)
    37: (8,  52, 472,  530, 592),   # identical figure (hexagon pot)
    48: (10, 52, 368,  530, 532),   # shape pattern (diagonal/circle/polygon)
    61: (12, 52, 364,  530, 452),   # odd one out (Flock/Bunch/Dozen/Group — text)
    62: (12, 52, 446,  530, 488),   # odd city (Mumbai/Kolkata/Jaipur/Nagpur — text)
    63: (12, 52, 480,  530, 592),   # odd shape figures (triangle/pentagon/shapes)
    64: (13, 52,  42,  530, 178),   # flower/vase shapes
    65: (13, 52, 172,  530, 206),   # number pattern (4415/2204/3254/2313 — text)
    67: (13, 52, 246,  530, 456),   # hexagon sequence with ?
}


async def main():
    from app.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    engine = create_async_engine(settings.DATABASE_URL)

    # Load image_only questions
    async with engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT id, question_no FROM questions "
                    "WHERE exam_id = :eid AND question_type = 'image_only' "
                    "ORDER BY question_no"
                ),
                {"eid": EXAM_ID},
            )
        ).mappings().all()
    questions = {r["question_no"]: r["id"] for r in rows}
    print(f"Found {len(questions)} image_only questions: {sorted(questions.keys())}")

    doc = fitz.open(PDF_PATH)
    mat = fitz.Matrix(ZOOM, ZOOM)

    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )

    updates = []
    skipped = []

    for q_no in sorted(questions):
        q_id = questions[q_no]

        if q_no not in QUESTION_CROPS:
            print(f"  Q{q_no} (id={q_id}): no crop config — skipping")
            skipped.append(q_no)
            continue

        page_idx, x0, y0, x1, y1 = QUESTION_CROPS[q_no]
        page = doc[page_idx]
        clip = fitz.Rect(x0, y0, x1, y1)
        pix = page.get_pixmap(matrix=mat, clip=clip)
        img_bytes = pix.tobytes("png")

        key = f"exams/{EXAM_ID}/questions/{q_id}/q{q_no}.png"
        s3.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=img_bytes,
            ContentType="image/png",
        )
        url = f"{settings.R2_PUBLIC_URL.rstrip('/')}/{key}"
        print(f"  Q{q_no} (id={q_id}): ✓ {url}")
        updates.append((q_id, url))

    # Bulk update DB
    if updates:
        async with engine.begin() as conn:
            for q_id, url in updates:
                await conn.execute(
                    text("UPDATE questions SET question_image_url = :url WHERE id = :id"),
                    {"url": url, "id": q_id},
                )
        print(f"\nUpdated {len(updates)} questions in DB.")

    if skipped:
        print(f"Skipped (no crop config): Q{skipped}")

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
