"""
Payment module schemas — Pydantic v2 request/response models.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PlanResponse(BaseModel):
    id: int
    name: str
    duration_months: int
    price_inr: int
    features: dict


class CreateOrderResponse(BaseModel):
    order_id: str        # Razorpay order id
    amount: int          # in paise (price_inr * 100)
    currency: str        # 'INR'
    key_id: str          # public Razorpay key for frontend checkout


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class SubscriptionStatusResponse(BaseModel):
    is_active: bool
    expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None
    plan_name: Optional[str] = None
    amount_paid: Optional[int] = None


class PaymentHistoryRow(BaseModel):
    id: str
    amount_inr: int
    currency: str
    status: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime


# ── Admin schemas ─────────────────────────────────────────────

class AppSettingResponse(BaseModel):
    key: str
    value: str
    type: str
    label: Optional[str] = None
    updated_at: Optional[datetime] = None


class UpdateSettingRequest(BaseModel):
    value: str


class AdminSubscriptionRow(BaseModel):
    id: str
    parent_id: str
    parent_name: Optional[str] = None
    plan_name: Optional[str] = None
    status: str
    amount_paid_inr: Optional[int] = None
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class ExtendSubscriptionRequest(BaseModel):
    months: int
