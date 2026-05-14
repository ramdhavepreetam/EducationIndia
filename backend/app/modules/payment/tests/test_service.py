"""
Tests for payment service — ADR-014.
Mocks Razorpay client and DB to test business logic only.
"""

import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.payment.service import PaymentService
from app.modules.payment.schemas import CreateOrderRequest, VerifyPaymentRequest
from app.shared.exceptions import BadRequest, NotFound

pytestmark = pytest.mark.asyncio


def _mock_plan():
    return {"id": 1, "name": "Standard Access", "duration_months": 5, "price_inr": 499, "features": {}, "entitlements": []}


class TestPaymentService:

    async def test_create_order_returns_razorpay_order_id(self):
        svc = PaymentService()
        parent_id = uuid4()
        db = AsyncMock()

        with patch("app.modules.payment.service.payment_repository") as mock_repo, \
             patch("app.modules.payment.service.get_client") as mock_rpay:

            mock_repo.get_plan_by_id = AsyncMock(return_value=_mock_plan())
            mock_repo.create_subscription = AsyncMock(return_value={"id": str(uuid4())})
            mock_repo.get_setting = AsyncMock(return_value="rzp_test_key")

            mock_client = MagicMock()
            mock_client.order.create.return_value = {"id": "order_test_123", "amount": 49900}
            mock_rpay.return_value = mock_client

            result = await svc.create_order(parent_id, db, CreateOrderRequest(plan_id=1))

            assert result.order_id == "order_test_123"
            assert result.amount == 49900
            assert result.currency == "INR"
            assert result.key_id == "rzp_test_key"

    async def test_verify_valid_signature_activates_subscription(self):
        svc = PaymentService()
        parent_id = uuid4()
        sub_id = uuid4()
        db = AsyncMock()

        order_id = "order_test_456"
        payment_id = "pay_test_789"
        secret = "test_secret"
        message = f"{order_id}|{payment_id}"
        signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

        request = VerifyPaymentRequest(
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            razorpay_signature=signature,
        )

        with patch("app.modules.payment.service.payment_repository") as mock_repo, \
             patch("app.modules.payment.service.settings") as mock_settings:

            mock_settings.RAZORPAY_KEY_SECRET = secret

            mock_repo.get_subscription_by_order_id = AsyncMock(return_value={
                "id": sub_id, "parent_id": str(parent_id), "status": "pending",
                "amount_paid_inr": 499,
            })
            mock_repo.get_setting = AsyncMock(return_value="5")
            mock_repo.activate_subscription = AsyncMock(return_value={})
            mock_repo.create_payment = AsyncMock(return_value={})
            mock_repo.get_active_subscriptions = AsyncMock(return_value=[{
                "expires_at": datetime.now(timezone.utc) + timedelta(days=150),
                "plan_name": "Standard Access", "amount_paid_inr": 499,
                "id": uuid4(),
            }])

            result = await svc.verify_and_activate(parent_id, request, db)
            assert result.is_active is True
            assert result.plan_name == "Standard Access"

    async def test_verify_invalid_signature_raises_bad_request(self):
        svc = PaymentService()
        db = AsyncMock()

        request = VerifyPaymentRequest(
            razorpay_order_id="order_xxx",
            razorpay_payment_id="pay_xxx",
            razorpay_signature="bad_signature",
        )

        with patch("app.modules.payment.service.settings") as mock_settings:
            mock_settings.RAZORPAY_KEY_SECRET = "real_secret"

            with pytest.raises(BadRequest, match="Invalid payment signature"):
                await svc.verify_and_activate(uuid4(), request, db)

    async def test_get_status_returns_none_for_no_subscription(self):
        svc = PaymentService()
        db = AsyncMock()

        with patch("app.modules.payment.service.payment_repository") as mock_repo:
            mock_repo.get_active_subscriptions = AsyncMock(return_value=[])

            result = await svc.get_status(uuid4(), db)
            assert result.is_active is False
            assert result.expires_at is None

    async def test_subscription_expires_correctly(self):
        svc = PaymentService()
        db = AsyncMock()

        with patch("app.modules.payment.service.payment_repository") as mock_repo:
            # Subscription expired 1 day ago
            mock_repo.get_active_subscriptions = AsyncMock(return_value=[])

            result = await svc.get_status(uuid4(), db)
            assert result.is_active is False
