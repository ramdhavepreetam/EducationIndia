"""Tests for exam event (test set) creation and auto-assignment on publish."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.catalog.schemas import CreateEventRequest


def test_create_event_request_schema():
    """CreateEventRequest validates required fields."""
    req = CreateEventRequest(
        title_en="MSCE 2024 Practice Set",
        std_class=5,
        year=2024,
        board_id=1,
        category_id=1,
    )
    assert req.year == 2024
    assert req.std_class == 5


def test_create_event_request_rejects_invalid_class():
    """std_class must be 5 or 8."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        CreateEventRequest(
            title_en="Bad",
            std_class=6,  # invalid
            year=2024,
            board_id=1,
            category_id=1,
        )
