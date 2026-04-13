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
    ) -> dict | None:
        """
        Conditional UPDATE — only activates if status is not already 'active'.
        Returns None if the row was already active (idempotent, not an error).
        This prevents the double-activation race condition: concurrent verify
        calls both see 'pending', but only one UPDATE wins because of the
        WHERE status != 'active' guard.
        """
        result = await db.execute(
            text("""
                UPDATE subscriptions
                SET status = 'active',
                    started_at = now(),
                    expires_at = :expires_at,
                    razorpay_payment_id = :rpay_id,
                    updated_at = now()
                WHERE id = :sid AND status != 'active'
                RETURNING *
            """),
            {
                "sid": str(subscription_id),
                "rpay_id": razorpay_payment_id,
                "expires_at": expires_at,
            },
        )
        row = result.mappings().first()
        return dict(row) if row else None

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
        """
        ON CONFLICT DO NOTHING on razorpay_payment_id prevents duplicate payment
        records if verify_payment is called twice concurrently for the same order.
        Returns the existing row on conflict so callers always get a usable dict.
        """
        result = await db.execute(
            text("""
                INSERT INTO payments
                    (subscription_id, parent_id, amount_inr, razorpay_order_id,
                     razorpay_payment_id, razorpay_signature, status, paid_at)
                VALUES
                    (:sub_id, :pid, :amount, :order_id, :pay_id, :sig, :status,
                     CASE WHEN :status = 'captured' THEN now() ELSE NULL END)
                ON CONFLICT (razorpay_payment_id) DO NOTHING
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
        row = result.mappings().first()
        if row:
            return dict(row)
        # Conflict — fetch the existing row
        existing = await db.execute(
            text("SELECT * FROM payments WHERE razorpay_payment_id = :pay_id"),
            {"pay_id": razorpay_payment_id},
        )
        return dict(existing.mappings().first())

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

    async def get_payment_history(
        self, db: AsyncSession, parent_id: UUID, page: int = 1, limit: int = 50
    ) -> list[dict]:
        result = await db.execute(
            text("""
                SELECT id, amount_inr, currency, status, razorpay_order_id,
                       razorpay_payment_id, paid_at, created_at
                FROM payments
                WHERE parent_id = :pid
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"pid": str(parent_id), "limit": limit, "offset": (page - 1) * limit},
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

    async def get_all_subscriptions_admin(
        self, db: AsyncSession, page: int = 1, limit: int = 50
    ) -> list[dict]:
        result = await db.execute(text("""
            SELECT s.id, s.parent_id, up.full_name AS parent_name,
                   sp.name AS plan_name, s.status, s.amount_paid_inr,
                   s.started_at, s.expires_at, s.created_at
            FROM subscriptions s
            LEFT JOIN user_profiles up ON up.id = s.parent_id
            LEFT JOIN subscription_plans sp ON sp.id = s.plan_id
            ORDER BY s.created_at DESC
            LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": (page - 1) * limit})
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

    # ── Admin analytics ──────────────────────────────────────────────────────

    async def get_payment_stats_admin(self, db: AsyncSession) -> dict:
        """Revenue summary stats for admin dashboard."""
        result = await db.execute(text("""
            SELECT
                COALESCE(SUM(CASE WHEN p.status = 'captured' THEN p.amount_inr ELSE 0 END), 0)
                    AS total_revenue_inr,
                COUNT(DISTINCT CASE WHEN s.status = 'active' AND s.expires_at > now() THEN s.id END)
                    AS active_subscriptions,
                COUNT(DISTINCT CASE WHEN s.status = 'expired' OR (s.status = 'active' AND s.expires_at <= now()) THEN s.id END)
                    AS expired_subscriptions,
                COUNT(DISTINCT CASE WHEN s.status = 'cancelled' THEN s.id END)
                    AS cancelled_subscriptions,
                COUNT(p.id)                                                     AS total_transactions,
                COUNT(CASE WHEN p.status = 'failed' THEN 1 END)                AS failed_transactions,
                COALESCE(SUM(CASE
                    WHEN p.status = 'captured'
                     AND date_trunc('month', p.paid_at) = date_trunc('month', now())
                    THEN p.amount_inr ELSE 0 END), 0)                          AS this_month_revenue,
                COALESCE(SUM(CASE
                    WHEN p.status = 'captured'
                     AND date_trunc('month', p.paid_at) = date_trunc('month', now() - interval '1 month')
                    THEN p.amount_inr ELSE 0 END), 0)                          AS last_month_revenue
            FROM subscriptions s
            FULL OUTER JOIN payments p ON p.subscription_id = s.id
        """))
        row = result.mappings().first()
        return dict(row) if row else {}

    async def get_all_payments_admin(
        self, db: AsyncSession,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> list[dict]:
        """All payment transactions with optional filters. Admin only."""
        conditions = []
        params: dict = {"offset": (page - 1) * limit, "limit": limit}

        if status and status != "all":
            conditions.append("p.status = :status")
            params["status"] = status
        if search:
            conditions.append("(up.full_name ILIKE :search OR au.email ILIKE :search)")
            params["search"] = f"%{search}%"

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        result = await db.execute(text(f"""
            SELECT p.id, p.amount_inr, p.currency, p.status,
                   p.razorpay_order_id, p.razorpay_payment_id,
                   p.failure_reason, p.paid_at, p.created_at,
                   up.full_name AS parent_name,
                   au.email    AS parent_email,
                   s.id        AS subscription_id
            FROM payments p
            LEFT JOIN subscriptions s  ON s.id  = p.subscription_id
            LEFT JOIN user_profiles up ON up.id = p.parent_id
            LEFT JOIN auth.users au    ON au.id = p.parent_id
            {where}
            ORDER BY p.created_at DESC
            LIMIT :limit OFFSET :offset
        """), params)
        return [dict(row) for row in result.mappings().all()]

    async def get_payments_by_parent_admin(
        self, db: AsyncSession, parent_id: str
    ) -> list[dict]:
        """All payments for a specific parent. Admin drill-down."""
        result = await db.execute(text("""
            SELECT p.id, p.amount_inr, p.currency, p.status,
                   p.razorpay_order_id, p.razorpay_payment_id,
                   p.failure_reason, p.paid_at, p.created_at,
                   s.expires_at AS subscription_expires_at
            FROM payments p
            LEFT JOIN subscriptions s ON s.id = p.subscription_id
            WHERE p.parent_id = :pid
            ORDER BY p.created_at DESC
        """), {"pid": parent_id})
        return [dict(row) for row in result.mappings().all()]

    async def get_monthly_revenue_admin(
        self, db: AsyncSession, months: int = 6
    ) -> list[dict]:
        """Month-by-month revenue for the last N months. Admin only."""
        result = await db.execute(text("""
            SELECT
                to_char(date_trunc('month', paid_at), 'YYYY-MM') AS month,
                COALESCE(SUM(amount_inr), 0)                     AS revenue,
                COUNT(*)                                         AS count
            FROM payments
            WHERE status = 'captured'
              AND paid_at >= date_trunc('month', now()) - ((:months - 1) || ' months')::interval
            GROUP BY date_trunc('month', paid_at)
            ORDER BY date_trunc('month', paid_at)
        """), {"months": months})
        return [dict(row) for row in result.mappings().all()]


# Module-level singleton
payment_repository = PaymentRepository()
