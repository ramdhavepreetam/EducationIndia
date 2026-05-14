"""
Payment module service — business logic for Razorpay order/verify/subscribe.

Rules:
  - Price always read from DB (subscription_plans.price_inr)
  - Razorpay key_secret from env only — never from DB
  - Signature verification uses HMAC-SHA256
  - Service calls repository; never writes raw SQL
"""

import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import UUID

from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.payment.razorpay_client import get_client
from app.modules.payment.repository import payment_repository
from app.modules.payment.schemas import (
    CreateOrderResponse,
    CreateOrderRequest,
    PlanCreateRequest,
    PlanEntitlementRequest,
    PlanResponse,
    PlanUpdateRequest,
    SubscriptionStatusResponse,
    VerifyPaymentRequest,
    PaymentHistoryRow,
)
from app.shared.exceptions import BadRequest, NotFound


class PaymentService:

    async def get_active_plan(self, db: AsyncSession) -> PlanResponse:
        plan = await payment_repository.get_active_plan(db)
        if not plan:
            raise NotFound("No active subscription plan found")
        return PlanResponse(**plan)

    async def get_active_plans(self, db: AsyncSession) -> list[PlanResponse]:
        """Returns active subscription plans with entitlement summaries."""
        plans = await payment_repository.get_active_plans(db)
        return [PlanResponse(**plan) for plan in plans]

    async def create_order(
        self, parent_id: UUID, db: AsyncSession, request: CreateOrderRequest
    ) -> CreateOrderResponse:
        """
        1. Load selected active plan (price from DB)
        2. Create Razorpay order
        3. Create pending subscription row
        4. Return order details for frontend checkout
        """
        plan = await payment_repository.get_plan_by_id(db, request.plan_id, active_only=True)
        if not plan:
            raise NotFound("No active subscription plan found")

        amount_paise = plan["price_inr"] * 100

        # Create Razorpay order
        client = get_client()
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": str(parent_id)[:40],
        })

        # Create pending subscription
        await payment_repository.create_subscription(
            db,
            parent_id=parent_id,
            plan_id=plan["id"],
            razorpay_order_id=order["id"],
            amount_paid_inr=plan["price_inr"],
        )

        # Read the public key from app_settings
        key_id = await payment_repository.get_setting(db, "razorpay_key_id")

        return CreateOrderResponse(
            order_id=order["id"],
            amount=amount_paise,
            currency="INR",
            key_id=key_id or settings.RAZORPAY_KEY_ID,
        )

    async def verify_and_activate(
        self, parent_id: UUID, request: VerifyPaymentRequest, db: AsyncSession
    ) -> SubscriptionStatusResponse:
        """
        Verify Razorpay HMAC signature, activate subscription, create payment record.
        """
        # 1. Verify signature
        message = f"{request.razorpay_order_id}|{request.razorpay_payment_id}"
        expected = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, request.razorpay_signature):
            raise BadRequest("Invalid payment signature")

        # 2. Load pending subscription
        sub = await payment_repository.get_subscription_by_order_id(
            db, request.razorpay_order_id
        )
        if not sub:
            raise NotFound("Subscription not found for this order")
        if str(sub["parent_id"]) != str(parent_id):
            raise NotFound("Subscription not found for this order")

        if sub["status"] == "active":
            # Idempotent — already activated (e.g. webhook beat the verify call)
            return await self.get_status(parent_id, db)

        # 3. Calculate expiry
        duration_months = int(sub.get("duration_months") or 5)
        expires_at = datetime.now(timezone.utc) + relativedelta(months=duration_months)

        # 4. Activate subscription (conditional UPDATE — returns None if already active,
        # which means a concurrent verify call beat us here; both outcomes are fine)
        await payment_repository.activate_subscription(
            db,
            subscription_id=sub["id"],
            razorpay_payment_id=request.razorpay_payment_id,
            expires_at=expires_at,
        )

        # 5. Create payment record (ON CONFLICT DO NOTHING — safe to call twice)
        await payment_repository.create_payment(
            db,
            subscription_id=sub["id"],
            parent_id=parent_id,
            amount_inr=sub["amount_paid_inr"],
            razorpay_order_id=request.razorpay_order_id,
            razorpay_payment_id=request.razorpay_payment_id,
            razorpay_signature=request.razorpay_signature,
            status="captured",
        )

        return await self.get_status(parent_id, db)

    async def get_status(
        self, parent_id: UUID, db: AsyncSession
    ) -> SubscriptionStatusResponse:
        """Active subscription status for a parent. Returns is_active=false if none."""
        subs = await payment_repository.get_active_subscriptions(db, parent_id)
        if not subs:
            return SubscriptionStatusResponse(is_active=False)

        sub = subs[0]
        days_remaining = None
        if sub["expires_at"]:
            delta = sub["expires_at"] - datetime.now(timezone.utc)
            days_remaining = max(0, delta.days)

        return SubscriptionStatusResponse(
            is_active=True,
            expires_at=sub["expires_at"],
            days_remaining=days_remaining,
            plan_name=sub.get("plan_name"),
            amount_paid=sub.get("amount_paid_inr"),
            active_subscriptions=[
                {
                    "id": str(row["id"]),
                    "plan_name": row.get("plan_name"),
                    "expires_at": row.get("expires_at"),
                    "amount_paid": row.get("amount_paid_inr"),
                }
                for row in subs
            ],
        )

    async def get_payment_history(
        self, parent_id: UUID, db: AsyncSession, page: int = 1, limit: int = 50
    ) -> list[PaymentHistoryRow]:
        rows = await payment_repository.get_payment_history(db, parent_id, page=page, limit=limit)
        return [PaymentHistoryRow(**{**r, "id": str(r["id"])}) for r in rows]

    async def create_plan(self, db: AsyncSession, data: PlanCreateRequest) -> PlanResponse:
        payload = data.model_dump(exclude={"entitlements"})
        payload["features_json"] = json.dumps(payload.pop("features") or {})
        plan = await payment_repository.create_plan(db, payload)
        for entitlement in data.entitlements:
            await payment_repository.add_plan_entitlement(
                db, plan["id"], entitlement.model_dump()
            )
        return PlanResponse(**(await payment_repository.get_plan_by_id(db, plan["id"])))

    async def update_plan(
        self, db: AsyncSession, plan_id: int, data: PlanUpdateRequest
    ) -> PlanResponse:
        payload = data.model_dump(exclude_unset=True)
        if "features" in payload:
            payload["features_json"] = json.dumps(payload.pop("features") or {})
        plan = await payment_repository.update_plan(db, plan_id, payload)
        if not plan:
            raise NotFound("Plan not found")
        return PlanResponse(**plan)

    async def add_plan_entitlement(
        self, db: AsyncSession, plan_id: int, data: PlanEntitlementRequest
    ) -> PlanResponse:
        plan = await payment_repository.get_plan_by_id(db, plan_id)
        if not plan:
            raise NotFound("Plan not found")
        await payment_repository.add_plan_entitlement(db, plan_id, data.model_dump())
        return PlanResponse(**(await payment_repository.get_plan_by_id(db, plan_id)))

    async def delete_plan_entitlement(
        self, db: AsyncSession, plan_id: int, entitlement_id: int
    ) -> PlanResponse:
        deleted = await payment_repository.delete_plan_entitlement(db, plan_id, entitlement_id)
        if not deleted:
            raise NotFound("Entitlement not found")
        return PlanResponse(**(await payment_repository.get_plan_by_id(db, plan_id)))


# Module-level singleton
payment_service = PaymentService()
