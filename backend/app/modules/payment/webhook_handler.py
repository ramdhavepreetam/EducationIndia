"""
Razorpay webhook handler — processes async payment events.

Webhook endpoint:
  - Excluded from JWT auth middleware
  - Signature verified BEFORE processing
  - Idempotent — safe to receive same event twice
  - Returns 200 always (Razorpay retries on non-200)

Events handled:
  payment.captured → activate subscription
  payment.failed   → mark payment as failed
  refund.created   → mark payment as refunded
"""

import hashlib
import hmac
import json
from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.payment.repository import payment_repository


async def handle_webhook(payload: bytes, signature: str, db: AsyncSession) -> dict:
    """
    Process a Razorpay webhook event.
    Returns a status dict (always 200 to Razorpay).
    """
    # 1. Verify webhook signature
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return {"status": "ignored", "reason": "invalid_signature"}

    # 2. Parse event
    data = json.loads(payload)
    event = data.get("event", "")

    if event == "payment.captured":
        return await _handle_payment_captured(data, db)
    elif event == "payment.failed":
        return await _handle_payment_failed(data, db)
    elif event == "refund.created":
        return await _handle_refund(data, db)

    return {"status": "ignored", "reason": f"unhandled_event: {event}"}


async def _handle_payment_captured(data: dict, db: AsyncSession) -> dict:
    """Activate subscription on successful payment capture."""
    entity = data.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = entity.get("order_id")
    payment_id = entity.get("id")

    if not order_id or not payment_id:
        return {"status": "ignored", "reason": "missing_ids"}

    # Find subscription
    sub = await payment_repository.get_subscription_by_order_id(db, order_id)
    if not sub:
        return {"status": "ignored", "reason": "subscription_not_found"}

    # Idempotent check
    if sub["status"] == "active":
        return {"status": "ok", "reason": "already_active"}

    # Calculate expiry
    duration_months = int(sub.get("duration_months") or 5)
    expires_at = datetime.now(timezone.utc) + relativedelta(months=duration_months)

    # Activate
    await payment_repository.activate_subscription(
        db,
        subscription_id=sub["id"],
        razorpay_payment_id=payment_id,
        expires_at=expires_at,
    )

    # Create payment record
    await payment_repository.create_payment(
        db,
        subscription_id=sub["id"],
        parent_id=sub["parent_id"],
        amount_inr=sub.get("amount_paid_inr", 0),
        razorpay_order_id=order_id,
        razorpay_payment_id=payment_id,
        razorpay_signature="",  # webhook doesn't have client signature
        status="captured",
    )

    return {"status": "ok", "subscription_id": str(sub["id"])}


async def _handle_payment_failed(data: dict, db: AsyncSession) -> dict:
    entity = data.get("payload", {}).get("payment", {}).get("entity", {})
    payment_id = entity.get("id")
    reason = entity.get("error_description", "Payment failed")

    if payment_id:
        await payment_repository.update_payment_status(
            db, payment_id, "failed", failure_reason=reason
        )

    return {"status": "ok", "action": "marked_failed"}


async def _handle_refund(data: dict, db: AsyncSession) -> dict:
    entity = data.get("payload", {}).get("refund", {}).get("entity", {})
    payment_id = entity.get("payment_id")

    if payment_id:
        await payment_repository.update_payment_status(db, payment_id, "refunded")

    return {"status": "ok", "action": "marked_refunded"}
