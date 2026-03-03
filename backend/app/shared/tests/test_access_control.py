"""
Tests for shared/access_control.py — ADR-014 gate functions.

Uses mock DB results to test gate logic without a live database.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.shared.access_control import (
    AccessContext,
    can_start_exam,
    can_see_full_analysis,
    can_download_pdf,
    get_tier,
)

pytestmark = pytest.mark.asyncio


def _ctx(is_paid: bool, free_exam_id: int = 1, free_max_attempts: int = 3):
    return AccessContext(
        parent_id=uuid4(),
        is_paid=is_paid,
        free_exam_id=free_exam_id,
        free_max_attempts=free_max_attempts,
    )


class TestCanStartExam:

    async def test_paid_user_can_access_all_exams(self):
        """Paid user can start any exam, including Paper II."""
        ctx = _ctx(is_paid=True)
        db = AsyncMock()
        allowed, reason = await can_start_exam(ctx, exam_id=2, child_profile_id=uuid4(), db=db)
        assert allowed is True
        assert reason == ""

    async def test_free_user_blocked_from_paper_II(self):
        """Free user cannot start Paper II (exam_id != free_tier_exam_id)."""
        ctx = _ctx(is_paid=False, free_exam_id=1)
        db = AsyncMock()
        allowed, reason = await can_start_exam(ctx, exam_id=2, child_profile_id=uuid4(), db=db)
        assert allowed is False
        assert reason == "upgrade_required_exam"

    async def test_free_user_allowed_paper_I(self):
        """Free user can start Paper I when under attempt limit."""
        ctx = _ctx(is_paid=False, free_exam_id=1, free_max_attempts=3)
        db = AsyncMock()

        # Mock: 1 completed attempt exists
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        db.execute = AsyncMock(return_value=mock_result)

        allowed, reason = await can_start_exam(ctx, exam_id=1, child_profile_id=uuid4(), db=db)
        assert allowed is True
        assert reason == ""

    async def test_free_user_blocked_after_max_attempts(self):
        """Free user blocked when max attempts reached."""
        ctx = _ctx(is_paid=False, free_exam_id=1, free_max_attempts=3)
        db = AsyncMock()

        # Mock: 3 completed attempts
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        db.execute = AsyncMock(return_value=mock_result)

        allowed, reason = await can_start_exam(ctx, exam_id=1, child_profile_id=uuid4(), db=db)
        assert allowed is False
        assert reason == "upgrade_required_attempts"


class TestAnalysisGates:

    def test_paid_user_sees_full_analysis(self):
        ctx = _ctx(is_paid=True)
        assert can_see_full_analysis(ctx) is True
        assert can_download_pdf(ctx) is True

    def test_free_user_sees_score_only(self):
        ctx = _ctx(is_paid=False)
        assert can_see_full_analysis(ctx) is False
        assert can_download_pdf(ctx) is False


class TestGetTier:

    def test_paid_tier(self):
        assert get_tier(_ctx(is_paid=True)) == "paid"

    def test_free_tier(self):
        assert get_tier(_ctx(is_paid=False)) == "free"
