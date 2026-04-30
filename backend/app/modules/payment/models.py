"""
Payment module models — maps to subscription_plans, subscriptions, payments tables.

Column names MUST match the Supabase migration exactly.
"""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Integer,
    SmallInteger,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class SubscriptionPlan(Base):
    """Active subscription plans — admin configurable."""
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    duration_months: Mapped[int] = mapped_column(SmallInteger, server_default="5")
    price_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    max_children: Mapped[int] = mapped_column(Integer, server_default="999")
    features: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )


class SubscriptionStatusEnum(str, enum.Enum):
    pending = "pending"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class Subscription(Base):
    """Per-parent subscription record — created on order, activated on payment."""
    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    parent_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    plan_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("subscription_plans.id"))
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    razorpay_order_id: Mapped[str | None] = mapped_column(Text, unique=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(Text)
    amount_paid_inr: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


class PaymentStatusEnum(str, enum.Enum):
    created = "created"
    captured = "captured"
    failed = "failed"
    refunded = "refunded"


class Payment(Base):
    """Individual payment record — one per Razorpay transaction."""
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    subscription_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("subscriptions.id"))
    parent_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    amount_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), server_default="INR")
    razorpay_order_id: Mapped[str | None] = mapped_column(Text)
    razorpay_payment_id: Mapped[str | None] = mapped_column(Text, unique=True)
    razorpay_signature: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), server_default="created")
    paid_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
