# ADR-005: Exam Attempt State Machine

**Date:** 2025-02-21
**Status:** Accepted
**Decider:** Preetam
**Modules Affected:** attempt (owns), analysis (reads), parent (reads)

---

## Context

An exam attempt has a lifecycle: it starts, responses are saved incrementally,
and it ends either by student submission or timer expiry. The system must handle
page refreshes (student must be able to resume), browser crashes (data must not
be lost), and timer enforcement (90 minutes is a hard limit). Multiple attempts
at the same exam must be tracked separately for progress analysis. The state
of every question (visited, answered, marked for review) must persist for the
question palette color coding. These requirements define a non-trivial state
machine that must be explicit and enforced.

---

## Decision

We will implement an explicit state machine in attempt/state_machine.py with
states: not_started → ongoing → submitted | expired | abandoned.
State transitions are the only way to change attempt.status. Auto-save
is implemented as individual response upserts (one API call per answer change),
not periodic full-state dumps. Timer is enforced client-side with server-side
validation on submit (compare started_at + duration to submitted_at).

---

## Alternatives Considered

### Option 1: Periodic full-state dump (autosave every 30 seconds)
Frontend sends all responses every 30 seconds as one payload.
- Pro: Simple — one endpoint handles everything
- Con: Data loss window of up to 30 seconds on crash
- Con: Large payload grows as student answers more questions
- Con: Race condition if student submits while autosave is in-flight

### Option 2: WebSocket real-time sync
Real-time bidirectional connection, every keystroke synced.
- Pro: Zero data loss
- Con: WebSocket infra complexity on Render free tier
- Con: Overkill — students answer one question at a time, not typing continuously
- Con: ADR-010 defers WebSockets to future consideration

### Option 3: Per-answer upsert (one API call per answer) ← CHOSEN
POST /api/attempts/{id}/responses — called when student selects an option.
- Pro: At most one question's answer lost on crash
- Pro: Small constant-size payload regardless of how many questions answered
- Pro: No race condition — each upsert is independent
- Con: More API calls total (up to 75 during exam) — acceptable for exam use

---

## Consequences

### Positive
- Student can refresh page and resume — all answers restored from DB
- No complex client-side persistence (no localStorage for answers)
- Timer can be validated server-side by comparing timestamps
- attempt_number field allows tracking improvement across multiple attempts

### Negative
- Per-answer API calls require good mobile network (exam environment)
- State machine adds complexity vs. simple CRUD — worth it for correctness

### Neutral
- attempts_used counter in exam_assignments updated by DB trigger on submit
- abandoned status set if student closes browser for > exam duration time

---

## Module Impact

```
attempt/state_machine.py   → transitions dict, validate_transition(), transition()
attempt/service.py         → calls state_machine.transition() for every status change
attempt/router.py          → POST /start, POST /{id}/responses (upsert), POST /{id}/submit
attempt/schemas.py         → AttemptStateResponse (returns full palette state for resume)
responses table            → visit_count, is_marked_review for palette state
attempts table             → status, started_at, submitted_at, last_saved_at
```

---

## Implementation Notes

State machine (attempt/state_machine.py):
```python
TRANSITIONS = {
    "not_started": ["ongoing"],
    "ongoing":     ["submitted", "expired", "abandoned"],
    "submitted":   [],           # Terminal — no transitions out
    "expired":     [],           # Terminal
    "abandoned":   ["ongoing"],  # Can resume if within time window
}

def validate_transition(current: str, target: str) -> bool:
    return target in TRANSITIONS.get(current, [])
```

Resume exam endpoint:
```
GET /api/attempts/{id}/state
Returns: {
  "attempt_id": "uuid",
  "time_remaining_seconds": 3240,
  "responses": [
    {"question_no": 1, "selected_option": 2,
     "is_marked_review": false, "visit_count": 1},
    ...
  ]
}
```

Timer enforcement:
```python
# On submit:
elapsed = (datetime.utcnow() - attempt.started_at).seconds
if elapsed > (exam.duration_minutes * 60) + 30:  # 30 second grace
    raise AttemptExpiredException()
```

Question palette state mapping:
```
visit_count=0, selected=None  → gray    (not visited)
visit_count>0, selected=None  → white   (visited, unanswered)
visit_count>0, selected!=None → green   (answered)
is_marked_review=True, None   → orange  (marked, unanswered)
is_marked_review=True, set    → purple  (marked + answered)
```

---

## Review Trigger

Revisit if offline exam support is needed (exams in areas with poor internet).
That would require local-first storage (IndexedDB) with sync on reconnect —
a fundamentally different architecture.
