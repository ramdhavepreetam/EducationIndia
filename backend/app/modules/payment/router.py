"""
Payment module router — HTTP layer only.

Endpoints:
  GET   /api/payment/plans        → Public. Active plan with price.
  GET   /api/payment/status       → Auth: parent. Subscription status.
  POST  /api/payment/create-order → Auth: parent. Creates Razorpay order.
  POST  /api/payment/verify       → Auth: parent. Verifies + activates.
  POST  /api/payment/webhook      → NO JWT. Razorpay webhook.
  GET   /api/payment/history      → Auth: parent. Payment records.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.dependencies import UserIdentity, verify_token
from app.modules.payment.schemas import (
    CreateOrderResponse,
    PaymentHistoryRow,
    PlanResponse,
    SubscriptionStatusResponse,
    VerifyPaymentRequest,
)
from app.modules.payment.service import payment_service
from app.modules.payment.webhook_handler import handle_webhook

router = APIRouter()


@router.get("/plans", response_model=PlanResponse)
async def get_plan(db: AsyncSession = Depends(get_db)):
    """
    Public — returns active plan with price.
    No auth required (show price on landing page).
    """
    return await payment_service.get_active_plan(db)


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_status(
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """Returns the calling parent's subscription status."""
    return await payment_service.get_status(identity.id, db)


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """Creates a Razorpay order and a pending subscription record."""
    return await payment_service.create_order(identity.id, db)


@router.post("/verify", response_model=SubscriptionStatusResponse)
async def verify_payment(
    request: VerifyPaymentRequest,
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """Verifies Razorpay signature and activates subscription."""
    return await payment_service.verify_and_activate(identity.id, request, db)


@router.post("/webhook")
async def webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Razorpay webhook — NO JWT auth.
    Signature verified inside handler.
    Always returns 200 (Razorpay retries on non-200).
    """
    payload = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    result = await handle_webhook(payload, signature, db)
    return result


@router.get("/history", response_model=list[PaymentHistoryRow])
async def get_history(
    db: AsyncSession = Depends(get_db),
    identity: UserIdentity = Depends(verify_token),
):
    """Returns the calling parent's payment history."""
    return await payment_service.get_payment_history(identity.id, db)
