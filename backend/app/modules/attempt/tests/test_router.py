"""
Attempt module router integration tests.

Uses FastAPI TestClient with:
  - get_db dependency overridden (→ AsyncMock session, no real DB)
  - verify_token dependency overridden (→ FAKE_IDENTITY, no JWT validation)
  - attempt_service patched per-test to control business logic responses

Tests HTTP layer only: status codes, request validation, response shapes, security.

Run: pytest backend/app/modules/attempt/tests/test_router.py -v
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.modules.attempt.schemas import (
    AttemptResultResponse,
    AttemptStateResponse,
    ResponseStateItem,
)
from app.modules.attempt.state_machine import AttemptAlreadySubmittedException
from app.shared.exceptions import Conflict, Forbidden, Unauthorized


# ── Constants ─────────────────────────────────────────────────────────────────

STUDENT_ID = uuid4()
ATTEMPT_ID = uuid4()
EXAM_ID = 1
NOW = datetime.now(timezone.utc)

FAKE_IDENTITY = MagicMock()
FAKE_IDENTITY.id = STUDENT_ID
FAKE_IDENTITY.role = "student"


# ── Test app factory ──────────────────────────────────────────────────────────

def get_test_app(identity=FAKE_IDENTITY):
    """
    Create a fully isolated test FastAPI app.
    Overrides both get_db (→ AsyncMock) and verify_token (→ identity).
    No real DB connection or JWT validation happens in any test.
    """
    from fastapi import FastAPI
    from app.database import get_db
    from app.modules.attempt.router import router
    from app.modules.auth.dependencies import verify_token
    from app.shared.exceptions import (
        ScholarPathException,
        scholarpath_exception_handler,
        generic_exception_handler,
    )

    async def override_get_db():
        yield AsyncMock()

    def override_verify_token():
        if identity is None:
            raise Unauthorized()
        return identity

    app = FastAPI()
    app.add_exception_handler(ScholarPathException, scholarpath_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    app.include_router(router, prefix="/api/attempts")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_token] = override_verify_token

    return app


# ── Schema helpers ────────────────────────────────────────────────────────────

def make_state_response(**kwargs) -> AttemptStateResponse:
    return AttemptStateResponse(
        attempt_id=kwargs.get("attempt_id", ATTEMPT_ID),
        exam_id=kwargs.get("exam_id", EXAM_ID),
        attempt_number=kwargs.get("attempt_number", 1),
        status=kwargs.get("status", "ongoing"),
        started_at=NOW,
        time_remaining_seconds=kwargs.get("time_remaining_seconds", 5400),
        responses=kwargs.get("responses", []),
    )


def make_result_response() -> AttemptResultResponse:
    return AttemptResultResponse(
        attempt_id=ATTEMPT_ID,
        exam_id=EXAM_ID,
        status="submitted",
        attempt_number=1,
        submitted_at=NOW,
        total_score=50,
        total_correct=25,
        total_wrong=10,
        total_skipped=40,
        percentage=33.33,
        grade="Below Average",
        section_scores=[],
        topic_scores=[],
        time_analysis={},
        recommendations=["stub"],
    )


# ── Tests: POST /api/attempts/start ──────────────────────────────────────────

class TestStartExamEndpoint:
    def test_returns_201_with_attempt_data(self):
        app = get_test_app()
        expected = make_state_response()

        with patch("app.modules.attempt.router.attempt_service") as mock_svc:
            mock_svc.start_exam = AsyncMock(return_value=expected)
            client = TestClient(app)
            resp = client.post(
                "/api/attempts/start",
                json={"exam_id": EXAM_ID},
            )

        assert resp.status_code == 201
        data = resp.json()
        assert "attempt_id" in data
        assert data["status"] == "ongoing"
        assert data["time_remaining_seconds"] == 5400
        assert data["responses"] == []

    def test_returns_409_if_ongoing_exists(self):
        app = get_test_app()

        with patch("app.modules.attempt.router.attempt_service") as mock_svc:
            mock_svc.start_exam = AsyncMock(
                side_effect=Conflict("already have an ongoing attempt")
            )
            client = TestClient(app)
            resp = client.post("/api/attempts/start", json={"exam_id": EXAM_ID})

        assert resp.status_code == 409

    def test_unauthenticated_returns_401(self):
        """verify_token raises Unauthorized when identity=None → 401."""
        app = get_test_app(identity=None)

        client = TestClient(app)
        resp = client.post("/api/attempts/start", json={"exam_id": EXAM_ID})

        assert resp.status_code == 401


# ── Tests: GET /api/attempts/{id}/state ──────────────────────────────────────

class TestGetExamStateEndpoint:
    def test_returns_all_saved_responses(self):
        app = get_test_app()
        responses = [
            ResponseStateItem(
                question_no=i, question_id=i,
                selected_option=1, is_marked_review=False, visit_count=1
            )
            for i in range(1, 6)
        ]
        expected = make_state_response(responses=responses)

        with patch("app.modules.attempt.router.attempt_service") as mock_svc:
            mock_svc.get_exam_state = AsyncMock(return_value=expected)
            client = TestClient(app)
            resp = client.get(f"/api/attempts/{ATTEMPT_ID}/state")

        assert resp.status_code == 200
        assert len(resp.json()["responses"]) == 5

    def test_returns_403_for_wrong_student(self):
        app = get_test_app()

        with patch("app.modules.attempt.router.attempt_service") as mock_svc:
            mock_svc.get_exam_state = AsyncMock(side_effect=Forbidden("does not belong"))
            client = TestClient(app)
            resp = client.get(f"/api/attempts/{ATTEMPT_ID}/state")

        assert resp.status_code == 403


# ── Tests: POST /api/attempts/{id}/responses ─────────────────────────────────

class TestSaveResponseEndpoint:
    def test_returns_200_with_state_item(self):
        app = get_test_app()
        item = ResponseStateItem(
            question_no=5, question_id=5,
            selected_option=3, is_marked_review=False, visit_count=2
        )

        with patch("app.modules.attempt.router.attempt_service") as mock_svc:
            mock_svc.save_response = AsyncMock(return_value=item)
            client = TestClient(app)
            resp = client.post(
                f"/api/attempts/{ATTEMPT_ID}/responses",
                json={"question_id": 5, "selected_option": 3},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["selected_option"] == 3
        assert data["visit_count"] == 2

    def test_selected_option_must_be_1_to_4(self):
        """selected_option=5 fails Pydantic Field(ge=1, le=4) validation → 422."""
        app = get_test_app()

        client = TestClient(app)
        resp = client.post(
            f"/api/attempts/{ATTEMPT_ID}/responses",
            json={"question_id": 1, "selected_option": 5},
        )

        assert resp.status_code == 422

    def test_returns_409_for_submitted_attempt(self):
        app = get_test_app()

        with patch("app.modules.attempt.router.attempt_service") as mock_svc:
            mock_svc.save_response = AsyncMock(
                side_effect=AttemptAlreadySubmittedException()
            )
            client = TestClient(app)
            resp = client.post(
                f"/api/attempts/{ATTEMPT_ID}/responses",
                json={"question_id": 1, "selected_option": 2},
            )

        assert resp.status_code == 409


# ── Tests: POST /api/attempts/{id}/submit ────────────────────────────────────

class TestSubmitExamEndpoint:
    def test_returns_score_on_success(self):
        app = get_test_app()
        expected = make_result_response()

        with patch("app.modules.attempt.router.attempt_service") as mock_svc:
            mock_svc.submit_exam = AsyncMock(return_value=expected)
            client = TestClient(app)
            resp = client.post(f"/api/attempts/{ATTEMPT_ID}/submit")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "submitted"
        assert data["total_score"] == 50
        assert "correct_option" not in data    # SECURITY CHECK

    def test_result_has_no_correct_option_field(self):
        """SECURITY: AttemptResultResponse schema must NEVER have correct_option (ADR-012)."""
        schema_fields = AttemptResultResponse.model_fields
        assert "correct_option" not in schema_fields, (
            "correct_option must NEVER appear in AttemptResultResponse — ADR-012 violation!"
        )

    def test_unauthenticated_submit_returns_401(self):
        app = get_test_app(identity=None)

        client = TestClient(app)
        resp = client.post(f"/api/attempts/{ATTEMPT_ID}/submit")

        assert resp.status_code == 401

    def test_returns_403_for_other_student_submit(self):
        app = get_test_app()

        with patch("app.modules.attempt.router.attempt_service") as mock_svc:
            mock_svc.submit_exam = AsyncMock(side_effect=Forbidden("belong to you"))
            client = TestClient(app)
            resp = client.post(f"/api/attempts/{ATTEMPT_ID}/submit")

        assert resp.status_code == 403
