# archive/

Historical one-off scripts and extracted data from the manual exam-seeding phase.

These predate the proper importer at
`backend/app/modules/question/pdf_importer.py` (POST `/api/admin/questions/pdf-import`)
and are **superseded by it**. They are kept for provenance and reproducibility of how the
2017–2025 MSCE / 8th-2025 data was originally seeded. They are **not maintained**, **not
imported by application code**, and connect to the database directly (via `.env`) rather
than through the app.

Do not run these against production. For new exams, use the PDF importer — see
`../UploadQuestionPDF.md`.

## Layout

- `import/` — year/paper bulk-import scripts (`import_20XX_full.py`, `bulk_import_8th*.py`,
  `init_*.py`, `insert_missing_intel_8th.py`)
- `render/` — PDF page-render scripts (`render_20XX.py`)
- `extract/` — PDF text/image extraction helpers
- `ops/` — one-off DB/admin utilities (`clear_db.py`, `create_admin*.py`, `apply_migration.py`,
  DB sanity checks, token helpers)
- `data/` — extracted answer keys and question JSON dumps used as import input
