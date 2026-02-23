# ADR-006: Score Computation Strategy

**Date:** 2025-02-21
**Status:** Accepted
**Decider:** Preetam
**Modules Affected:** analysis (owns computation), attempt (triggers), parent, admin (read results)

---

## Context

After a student submits an exam, the system must calculate: total score,
section-wise scores, topic-wise performance, time analysis, a grade, and
personalised recommendations. This analysis is complex enough to be its own
module. The question is when to compute it and where to store it.
Two competing concerns: (1) result pages must load fast (students/parents
are eager after submission); (2) analysis logic must be testable without
a live database. The analysis module must also power the parent dashboard
showing progress over multiple attempts, and the admin report showing
class-wide performance.

---

## Decision

We will compute all analysis synchronously at submission time and store the
results as JSONB columns in the attempts table (section_scores, topic_scores,
time_analysis, recommendations). The analysis module's core functions
(scorer.py, recommender.py) are pure functions that take Python objects —
no database access, fully unit-testable. Analysis module reads responses
and questions read-only; it never writes to any table except by returning
values that attempt/service.py stores during submission.

---

## Alternatives Considered

### Option 1: Compute analysis on every result page load
No storage — always recalculate from raw responses on demand.
- Pro: Always fresh, no storage overhead
- Con: Heavy computation on every page visit (topic performance requires
  joining responses + questions + topics)
- Con: Parent dashboard showing 10 attempts = 10 expensive computations

### Option 2: Async background job after submission
Submit returns immediately, analysis runs in background worker (Celery).
- Pro: Faster submission response time
- Con: Result page shows "calculating..." state for unknown duration
- Con: Requires Celery + Redis — significant infra complexity
- Con: Overkill: 75 questions × simple arithmetic ≈ milliseconds

### Option 3: Synchronous computation stored as JSONB ← CHOSEN
Compute everything at submit time, store in attempts table.
- Pro: Result page is instant — just read JSONB columns
- Pro: Parent dashboard reads stored summaries — zero recomputation
- Pro: Pure functions in scorer.py are 100% unit-testable with no DB
- Pro: 75 questions take < 10ms to score — no perceptible delay
- Con: Analysis results are immutable after submission (by design)
- Con: If scoring logic bug found, historical results cannot auto-fix

---

## Consequences

### Positive
- Result page GET /api/analysis/attempts/{id}/report is a single DB read
- Parent dashboard loads fast — summaries pre-computed
- scorer.py has zero database dependencies — easy to write exhaustive tests
- Recommendations array is stored — no need to re-run recommender on every load

### Negative
- Bug in scorer.py at launch means wrong results stored forever for those attempts
- Requires careful testing before go-live (covered by test_scorer.py priority tests)
- JSONB column changes require data migration for historical attempts

### Neutral
- analysis module has no SQLAlchemy models (read-only, no ownership)
- grade thresholds: Excellent ≥ 90%, Good ≥ 70%, Average ≥ 50%, Below Average < 50%
- topic status thresholds: strong ≥ 70%, average ≥ 50%, weak < 50%

---

## Module Impact

```
analysis/scorer.py        → Pure functions: calculate_score(), calculate_topic_performance(),
                             calculate_time_analysis(), generate_grade()
analysis/recommender.py   → Pure function: generate_recommendations(topic_performance)
analysis/service.py       → Orchestrates scorer + recommender, reads from DB
analysis/router.py        → GET /api/analysis/attempts/{id}/report (read JSONB)
analysis/schemas.py       → ReportSchema, TopicPerformance, TimeAnalysis
attempt/service.py        → Calls analysis.service.generate_report() during submit(),
                             stores result back into attempts JSONB columns
question_stats table      → Updated by separate DB trigger (not by analysis module)
```

---

## Implementation Notes

Pure scorer functions (analysis/scorer.py) — no imports from other modules:
```python
from typing import List
from dataclasses import dataclass

@dataclass
class ResponseData:
    question_no: int
    question_id: int
    selected_option: int | None
    correct_option: int
    topic_id: int
    marks: int
    time_taken_seconds: int | None

def calculate_score(responses: List[ResponseData]) -> dict:
    correct = sum(1 for r in responses if r.selected_option == r.correct_option)
    wrong   = sum(1 for r in responses if r.selected_option and r.selected_option != r.correct_option)
    skipped = sum(1 for r in responses if r.selected_option is None)
    total_marks = sum(r.marks for r in responses)
    score = correct * 2  # 2 marks per correct answer
    return {
        "score": score,
        "total_marks": total_marks,
        "correct": correct,
        "wrong": wrong,
        "skipped": skipped,
        "percentage": round((score / total_marks * 100), 2) if total_marks else 0
    }

def generate_grade(percentage: float) -> str:
    if percentage >= 90: return "Excellent"
    if percentage >= 70: return "Good"
    if percentage >= 50: return "Average"
    return "Below Average"
```

Recommendation generation (analysis/recommender.py):
```python
WEAK_THRESHOLD = 50.0
STRONG_THRESHOLD = 70.0

def generate_recommendations(topic_performance: List[dict]) -> List[str]:
    recs = []
    for topic in topic_performance:
        if topic["percentage"] < WEAK_THRESHOLD:
            recs.append(
                f"Practice more {topic['name_en']} — "
                f"you scored {topic['percentage']:.0f}% in this topic."
            )
    if not recs:
        recs.append("Great performance! Keep practicing to maintain your scores.")
    return recs
```

---

## Review Trigger

Revisit when concurrent exam submissions exceed 50/minute and synchronous
computation creates submission latency. That's the signal to move to async
background processing with Celery. Also revisit if scoring rules change
(e.g. negative marking introduced) — update scorer.py and add migration
to flag historical attempts as "scored under old rules".
