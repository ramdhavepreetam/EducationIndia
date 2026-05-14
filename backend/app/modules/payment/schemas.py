"""
Payment module schemas — Pydantic v2 request/response models.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


ScopeType = Literal["all", "board", "category", "std_class", "event", "exam"]


class PlanEntitlementResponse(BaseModel):
    id: int
    scope_type: ScopeType
    board_id: Optional[int] = None
    category_id: Optional[int] = None
    std_class: Optional[int] = None
    event_id: Optional[int] = None
    exam_id: Optional[int] = None
    label: Optional[str] = None


class PlanResponse(BaseModel):
    id: int
    name: str
    duration_months: int
    price_inr: int
    features: dict
    description_en: Optional[str] = None
    description_mr: Optional[str] = None
    display_order: int = 1
    entitlements: list[PlanEntitlementResponse] = []


class CreateOrderRequest(BaseModel):
    plan_id: int


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
    active_subscriptions: list[dict] = []


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
    id: Optional[str] = None
    parent_id: str
    parent_name: Optional[str] = None
    parent_email: Optional[str] = None
    plan_name: Optional[str] = None
    status: str
    amount_paid_inr: Optional[int] = None
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class ExtendSubscriptionRequest(BaseModel):
    months: int


class PlanEntitlementRequest(BaseModel):
    scope_type: ScopeType
    board_id: Optional[int] = None
    category_id: Optional[int] = None
    std_class: Optional[int] = None
    event_id: Optional[int] = None
    exam_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_scope_target(self) -> "PlanEntitlementRequest":
        target_map = {
            "all": None,
            "board": self.board_id,
            "category": self.category_id,
            "std_class": self.std_class,
            "event": self.event_id,
            "exam": self.exam_id,
        }
        target = target_map[self.scope_type]
        if self.scope_type == "all":
            return self
        if target is None:
            raise ValueError(f"{self.scope_type} entitlement requires its matching target")
        return self


class PlanCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    duration_months: int = Field(default=5, ge=1, le=120)
    price_inr: int = Field(ge=0)
    description_en: Optional[str] = None
    description_mr: Optional[str] = None
    display_order: int = Field(default=1, ge=0)
    features: dict = {}
    entitlements: list[PlanEntitlementRequest] = []


class PlanUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    duration_months: Optional[int] = Field(default=None, ge=1, le=120)
    price_inr: Optional[int] = Field(default=None, ge=0)
    description_en: Optional[str] = None
    description_mr: Optional[str] = None
    display_order: Optional[int] = Field(default=None, ge=0)
    features: Optional[dict] = None
    is_active: Optional[bool] = None
