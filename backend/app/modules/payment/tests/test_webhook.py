"""
Tests for webhook handler — ADR-014.
Mocks DB to test webhook event processing logic.
"""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.payment.webhook_handler import handle_webhook

pytestmark = pytest.mark.asyncio


def _make_payload(event: str, entity: dict, entity_key: str = "payment"):
    return json.dumps({
        "event": event,
        "payload": {entity_key: {"entity": entity}},
    }).encode()


def _sign(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


class TestWebhookHandler:

    async def test_webhook_invalid_signature_ignored(self):
        db = AsyncMock()
        payload = _make_payload("payment.captured", {"id": "pay_1", "order_id": "order_1"})

        with patch("app.modules.payment.webhook_handler.settings") as mock_settings:
            mock_settings.RAZORPAY_WEBHOOK_SECRET = "real_secret"
            result = await handle_webhook(payload, "bad_sig", db)

        assert result["status"] == "ignored"
        assert result["reason"] == "invalid_signature"

    async def test_webhook_payment_captured_activates_sub(self):
        db = AsyncMock()
        secret = "webhook_secret"
        sub_id = uuid4()

        entity = {"id": "pay_captured_1", "order_id": "order_captured_1"}
        payload = _make_payload("payment.captured", entity)
        signature = _sign(payload, secret)

        with patch("app.modules.payment.webhook_handler.settings") as mock_settings, \
             patch("app.modules.payment.webhook_handler.payment_repository") as mock_repo:

            mock_settings.RAZORPAY_WEBHOOK_SECRET = secret
            mock_repo.get_subscription_by_order_id = AsyncMock(return_value={
                "id": sub_id, "parent_id": str(uuid4()), "status": "pending",
                "amount_paid_inr": 499,
            })
            mock_repo.get_setting = AsyncMock(return_value="5")
            mock_repo.activate_subscription = AsyncMock(return_value={})
            mock_repo.create_payment = AsyncMock(return_value={})

            result = await handle_webhook(payload, signature, db)

        assert result["status"] == "ok"
        assert result["subscription_id"] == str(sub_id)

    async def test_webhook_idempotent_on_duplicate_event(self):
        db = AsyncMock()
        secret = "webhook_secret"

        entity = {"id": "pay_dup_1", "order_id": "order_dup_1"}
        payload = _make_payload("payment.captured", entity)
        signature = _sign(payload, secret)

        with patch("app.modules.payment.webhook_handler.settings") as mock_settings, \
             patch("app.modules.payment.webhook_handler.payment_repository") as mock_repo:

            mock_settings.RAZORPAY_WEBHOOK_SECRET = secret
            mock_repo.get_subscription_by_order_id = AsyncMock(return_value={
                "id": uuid4(), "parent_id": str(uuid4()), "status": "active",  # Already active
                "amount_paid_inr": 499,
            })

            result = await handle_webhook(payload, signature, db)

        assert result["status"] == "ok"
        assert result["reason"] == "already_active"
