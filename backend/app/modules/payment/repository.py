"""
Payment module repository — DB operations only, no business logic.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PaymentRepository:

    async def get_active_plan(self, db: AsyncSession) -> dict | None:
        result = await db.execute(text("""
            SELECT id, name, duration_months, price_inr, features
            FROM subscription_plans
            WHERE is_active = true
            ORDER BY id
            LIMIT 1
        """))
        row = result.mappings().first()
        return dict(row) if row else None

    async def create_subscription(
        self, db: AsyncSession, *, parent_id: UUID, plan_id: int,
        razorpay_order_id: str, amount_paid_inr: int,
    ) -> dict:
        result = await db.execute(
            text("""
                INSERT INTO subscriptions (parent_id, plan_id, razorpay_order_id, amount_paid_inr, status)
                VALUES (:parent_id, :plan_id, :razorpay_order_id, :amount, 'pending')
                RETURNING id, parent_id, plan_id, status, razorpay_order_id, amount_paid_inr, created_at
            """),
            {
                "parent_id": str(parent_id),
                "plan_id": plan_id,
                "razorpay_order_id": razorpay_order_id,
                "amount": amount_paid_inr,
            },
        )
        return dict(result.mappings().first())

    async def get_subscription_by_order_id(self, db: AsyncSession, order_id: str) -> dict | None:
        result = await db.execute(
            text("SELECT * FROM subscriptions WHERE razorpay_order_id = :oid"),
            {"oid": order_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def activate_subscription(
        self, db: AsyncSession, *, subscription_id: UUID,
        razorpay_payment_id: str, expires_at: datetime,
    ) -> dict:
        result = await db.execute(
            text("""
                UPDATE subscriptions
                SET status = 'active',
                    started_at = now(),
                    expires_at = :expires_at,
                    razorpay_payment_id = :rpay_id,
                    updated_at = now()
                WHERE id = :sid
                RETURNING *
            """),
            {
                "sid": str(subscription_id),
                "rpay_id": razorpay_payment_id,
                "expires_at": expires_at,
            },
        )
        return dict(result.mappings().first())

    async def get_active_subscription(self, db: AsyncSession, parent_id: UUID) -> dict | None:
        result = await db.execute(
            text("""
                SELECT s.*, sp.name as plan_name
                FROM subscriptions s
                LEFT JOIN subscription_plans sp ON sp.id = s.plan_id
                WHERE s.parent_id = :pid AND s.status = 'active' AND s.expires_at > now()
                ORDER BY s.expires_at DESC
                LIMIT 1
            """),
            {"pid": str(parent_id)},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def create_payment(
        self, db: AsyncSession, *, subscription_id: UUID, parent_id: UUID,
        amount_inr: int, razorpay_order_id: str, razorpay_payment_id: str,
        razorpay_signature: str, status: str = "captured",
    ) -> dict:
        result = await db.execute(
            text("""
                INSERT INTO payments
                    (subscription_id, parent_id, amount_inr, razorpay_order_id,
                     razorpay_payment_id, razorpay_signature, status, paid_at)
                VALUES
                    (:sub_id, :pid, :amount, :order_id, :pay_id, :sig, :status,
                     CASE WHEN :status = 'captured' THEN now() ELSE NULL END)
                RETURNING *
            """),
            {
                "sub_id": str(subscription_id),
                "pid": str(parent_id),
                "amount": amount_inr,
                "order_id": razorpay_order_id,
                "pay_id": razorpay_payment_id,
                "sig": razorpay_signature,
                "status": status,
            },
        )
        return dict(result.mappings().first())

    async def update_payment_status(
        self, db: AsyncSession, razorpay_payment_id: str,
        status: str, failure_reason: str | None = None,
    ):
        await db.execute(
            text("""
                UPDATE payments
                SET status = :status, failure_reason = :reason
                WHERE razorpay_payment_id = :rpay_id
            """),
            {"status": status, "reason": failure_reason, "rpay_id": razorpay_payment_id},
        )

    async def get_payment_history(self, db: AsyncSession, parent_id: UUID) -> list[dict]:
        result = await db.execute(
            text("""
                SELECT id, amount_inr, currency, status, razorpay_order_id,
                       razorpay_payment_id, paid_at, created_at
                FROM payments
                WHERE parent_id = :pid
                ORDER BY created_at DESC
            """),
            {"pid": str(parent_id)},
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_setting(self, db: AsyncSession, key: str) -> str | None:
        result = await db.execute(
            text("SELECT value FROM app_settings WHERE key = :k"),
            {"k": key},
        )
        row = result.scalar()
        return row

    async def get_all_settings(self, db: AsyncSession) -> list[dict]:
        result = await db.execute(text(
            "SELECT key, value, type, label, updated_at FROM app_settings ORDER BY key"
        ))
        return [dict(row) for row in result.mappings().all()]

    async def update_setting(self, db: AsyncSession, key: str, value: str, admin_id: UUID):
        await db.execute(
            text("""
                UPDATE app_settings
                SET value = :val, updated_at = now(), updated_by = :uid
                WHERE key = :k
            """),
            {"val": value, "uid": str(admin_id), "k": key},
        )

    async def get_all_subscriptions_admin(self, db: AsyncSession) -> list[dict]:
        result = await db.execute(text("""
            SELECT s.id, s.parent_id, up.full_name AS parent_name,
                   sp.name AS plan_name, s.status, s.amount_paid_inr,
                   s.started_at, s.expires_at, s.created_at
            FROM subscriptions s
            LEFT JOIN user_profiles up ON up.id = s.parent_id
            LEFT JOIN subscription_plans sp ON sp.id = s.plan_id
            ORDER BY s.created_at DESC
        """))
        return [dict(row) for row in result.mappings().all()]

    async def extend_subscription(self, db: AsyncSession, sub_id: UUID, months: int) -> dict:
        result = await db.execute(
            text("""
                UPDATE subscriptions
                SET expires_at = expires_at + (:months || ' months')::interval,
                    updated_at = now()
                WHERE id = :sid
                RETURNING *
            """),
            {"sid": str(sub_id), "months": months},
        )
        return dict(result.mappings().first())

    async def cancel_subscription(self, db: AsyncSession, sub_id: UUID) -> dict:
        result = await db.execute(
            text("""
                UPDATE subscriptions
                SET status = 'cancelled',
                    updated_at = now()
                WHERE id = :sid
                RETURNING *
            """),
            {"sid": str(sub_id)},
        )
        return dict(result.mappings().first())

    async def sync_plan_price(self, db: AsyncSession, price_inr: int):
        """Sync subscription_plans.price_inr when admin updates app_settings."""
        await db.execute(
            text("UPDATE subscription_plans SET price_inr = :p WHERE is_active = true"),
            {"p": price_inr},
        )

    async def grant_subscription(
        self, db: AsyncSession, parent_id: str, plan_id: int, months: int
    ) -> dict:
        """Admin grants a subscription manually. Creates an active subscription."""
        result = await db.execute(
            text("""
                INSERT INTO subscriptions
                    (parent_id, plan_id, status, started_at, expires_at,
                     amount_paid_inr, razorpay_order_id, created_at, updated_at)
                VALUES
                    (:pid, :plan_id, 'active', now(),
                     now() + make_interval(months => :months),
                     0, 'admin_grant_' || gen_random_uuid()::text, now(), now())
                RETURNING *
            """),
            {"pid": parent_id, "plan_id": plan_id, "months": months},
        )
        row = result.mappings().first()
        if not row:
            return {}
        return dict(row)

    async def find_parent_by_email(self, db: AsyncSession, email: str) -> dict | None:
        """Find a parent user by email for admin grant flow."""
        result = await db.execute(
            text("""
                SELECT up.id, up.full_name, au.email, up.role
                FROM user_profiles up
                JOIN auth.users au ON au.id = up.id
                WHERE au.email = :email AND up.role = 'parent'
            """),
            {"email": email},
        )
        row = result.mappings().first()
        return dict(row) if row else None


# Module-level singleton
payment_repository = PaymentRepository()
