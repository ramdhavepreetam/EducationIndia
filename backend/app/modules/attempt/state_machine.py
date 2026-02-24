"""
Attempt state machine — the only authorised way to change attempt.status.

ADR-005 transition graph:
  not_started → ongoing
  ongoing     → submitted | expired | abandoned
  submitted   → (terminal — no transitions out)
  expired     → (terminal — no transitions out)
  abandoned   → ongoing   (student can resume if within time window)

Usage:
  from app.modules.attempt.state_machine import transition

  attempt = await transition(attempt, "submitted", db)
  # sets submitted_at, duration_seconds, persists status

Never call:  attempt.status = "submitted"  directly
Always call: transition(attempt, "submitted", db)
"""

from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.exceptions import BadRequest, Conflict


# ── Allowed transitions (ADR-005) ─────────────────────────────────────────────

TRANSITIONS: dict[str, list[str]] = {
    "not_started": ["ongoing"],
    "ongoing":     ["submitted", "expired", "abandoned"],
    "submitted":   [],          # terminal
    "expired":     [],          # terminal
    "abandoned":   ["ongoing"],
}


# ── Custom exceptions ─────────────────────────────────────────────────────────

class InvalidTransitionException(BadRequest):
    """Raised when a requested state transition is not allowed."""
    def __init__(self, current: str, target: str):
        super().__init__(
            f"Cannot transition attempt from '{current}' to '{target}'. "
            f"Allowed from '{current}': {TRANSITIONS.get(current, [])}"
        )


class AttemptAlreadySubmittedException(Conflict):
    """Raised when student tries to submit or modify a submitted attempt."""
    def __init__(self):
        super().__init__(
            "This attempt has already been submitted and cannot be modified."
        )


# ── State machine functions ───────────────────────────────────────────────────

def validate_transition(current: str, target: str) -> bool:
    """
    Return True if the transition current → target is allowed.
    Pure function — no DB access, safe to call in tests without a session.
    """
    return target in TRANSITIONS.get(current, [])


async def transition(attempt, target: str, db: AsyncSession):
    """
    Perform a validated state transition on an Attempt ORM object.

    Mutates attempt.status in-place and persists the update to the DB.
    Sets additional timestamps on specific transitions:
      → submitted: sets submitted_at, computes duration_seconds
      → expired:   sets submitted_at (records when expiry was detected)

    Raises:
      AttemptAlreadySubmittedException if current status = 'submitted'
      InvalidTransitionException if transition is not in TRANSITIONS

    Returns the mutated attempt object (same reference, updated fields).
    """
    current = str(attempt.status.value) if hasattr(attempt.status, "value") else str(attempt.status)

    # Attempting to modify an already-submitted attempt
    if current == "submitted":
        raise AttemptAlreadySubmittedException()

    if not validate_transition(current, target):
        raise InvalidTransitionException(current, target)

    now = datetime.now(timezone.utc)
    extra_updates: dict = {"status": target}

    if target == "submitted":
        extra_updates["submitted_at"] = now
        # Compute duration — how long student actually spent on the exam
        started = attempt.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        extra_updates["duration_seconds"] = max(0, int((now - started).total_seconds()))

    elif target == "expired":
        # Record when the expiry was detected (helps diagnose edge cases)
        extra_updates["submitted_at"] = now

    # Apply to ORM object (for in-memory consistency)
    attempt.status = target
    for field, value in extra_updates.items():
        setattr(attempt, field, value)

    # Persist to DB
    from app.modules.attempt.models import Attempt
    await db.execute(
        update(Attempt)
        .where(Attempt.id == attempt.id)
        .values(**extra_updates)
    )
    await db.flush()

    return attempt
