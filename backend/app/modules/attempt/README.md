# Attempt Module

Handles the full exam attempt lifecycle: start → autosave → submit.

## Ownership

| Resource | Table |
|----------|-------|
| Attempts | `attempts` |
| Responses | `responses` |

**Reads from:** `exams` (via catalog module), `questions` (for scoring), `exam_assignments`
**Writes to:** `attempts`, `responses`
**Never writes:** `question_stats` — updated by DB trigger on `status → submitted`

---

## State Machine (ADR-005)

```
not_started → ongoing → submitted  (terminal)
                     → expired    (terminal)
                     → abandoned
abandoned   → ongoing
```

All transitions go through `state_machine.transition()` — **never** set `attempt.status` directly.

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/attempts/start` | student | Start new attempt |
| `GET`  | `/api/attempts/` | student | List attempts for exam |
| `GET`  | `/api/attempts/{id}/state` | owner | Resume state |
| `POST` | `/api/attempts/{id}/responses` | owner | Autosave one answer |
| `POST` | `/api/attempts/{id}/submit` | owner | Submit + score |

---

## Autosave Design

One API call per answer change. The `/responses` endpoint is called up to **75 times per exam**.

- Uses `INSERT ... ON CONFLICT DO UPDATE` (upsert) — no race conditions
- `visit_count` increments on every call (drives palette colour)
- `first_visited_at` preserved on conflict (SQL `COALESCE`)
- `answered_at` set only when `selected_option` is not null

---

## Score Computation (ADR-006)

Scores are computed **synchronously** at submit time and stored as JSONB:

- `section_scores` — per-section breakdown
- `topic_scores` — per-topic with `strong/average/weak` status
- `time_analysis` — fastest/slowest question, avg time
- `recommendations` — generated from weak topics

**Day 7 stub:** Basic correct/wrong/skipped count only.
**Day 9:** Full `AnalysisService.generate_report()` wired in.

Scores are **never recomputed** after submission. Result page reads from stored JSONB.

---

## Security

- `correct_option` is fetched server-side in `service.py` → `_load_questions_with_answers()`
- It flows **only** into `_compute_result_stub()` and is stored as aggregate stats
- `AttemptResultResponse` has **no** `correct_option` field
- Per-question review requires `GET /api/questions/{id}/review?attempt_id=...` with `status=submitted` gate

---

## Timer Enforcement

- Client-side countdown synced from `time_remaining_seconds` in `AttemptStateResponse`
- On submit: server checks `(submitted_at - started_at) > duration_minutes * 60 + 30`
- **30-second grace period** to account for network latency
- On page resume: if elapsed > duration, auto-transition to `expired`

---

## Files

```
attempt/
├── models.py        — Attempt, Response ORM models
├── schemas.py       — 6 Pydantic schemas
├── repository.py    — All DB queries
├── service.py       — Business logic + stub scorer
├── state_machine.py — Transition enforcement
├── router.py        — 5 HTTP endpoints
└── tests/
    ├── test_state_machine.py
    ├── test_service.py
    └── test_router.py
```

---

## Running Tests

```bash
cd backend
pytest app/modules/attempt/tests/ -v
```
