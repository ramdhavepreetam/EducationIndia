"""
Payment module repository — DB operations only, no business logic.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PaymentRepository:

    _plan_select = """
        SELECT
            sp.id,
            sp.name,
            sp.duration_months,
            sp.price_inr,
            sp.features,
            sp.description_en,
            sp.description_mr,
            sp.display_order,
            sp.is_active,
            sp.created_at,
            COALESCE(
                jsonb_agg(
                    jsonb_build_object(
                        'id', spe.id,
                        'scope_type', spe.scope_type,
                        'board_id', spe.board_id,
                        'category_id', spe.category_id,
                        'std_class', spe.std_class,
                        'event_id', spe.event_id,
                        'exam_id', spe.exam_id,
                        'label',
                            CASE
                                WHEN spe.scope_type = 'all' THEN 'All exams'
                                WHEN spe.scope_type = 'board' THEN eb.name_en
                                WHEN spe.scope_type = 'category' THEN ec.name_en
                                WHEN spe.scope_type = 'std_class' THEN 'Class ' || spe.std_class::text
                                WHEN spe.scope_type = 'event' THEN ee.title_en
                                WHEN spe.scope_type = 'exam' THEN ex.title_en
                                ELSE spe.scope_type
                            END
                    )
                    ORDER BY spe.id
                ) FILTER (WHERE spe.id IS NOT NULL),
                '[]'::jsonb
            ) AS entitlements
        FROM subscription_plans sp
        LEFT JOIN subscription_plan_entitlements spe ON spe.plan_id = sp.id
        LEFT JOIN exam_boards eb ON eb.id = spe.board_id
        LEFT JOIN exam_categories ec ON ec.id = spe.category_id
        LEFT JOIN exam_events ee ON ee.id = spe.event_id
        LEFT JOIN exams ex ON ex.id = spe.exam_id
    """

    async def get_active_plan(self, db: AsyncSession) -> dict | None:
        plans = await self.get_active_plans(db)
        return plans[0] if plans else None

    async def get_active_plans(self, db: AsyncSession) -> list[dict]:
        result = await db.execute(text(f"""
            {self._plan_select}
            WHERE sp.is_active = true
            GROUP BY sp.id
            ORDER BY sp.display_order, sp.id
        """))
        return [dict(row) for row in result.mappings().all()]

    async def get_all_plans_admin(self, db: AsyncSession) -> list[dict]:
        result = await db.execute(text(f"""
            {self._plan_select}
            GROUP BY sp.id
            ORDER BY sp.is_active DESC, sp.display_order, sp.id
        """))
        return [dict(row) for row in result.mappings().all()]

    async def get_plan_by_id(
        self, db: AsyncSession, plan_id: int, *, active_only: bool = False
    ) -> dict | None:
        where = "WHERE sp.id = :plan_id"
        if active_only:
            where += " AND sp.is_active = true"
        result = await db.execute(text(f"""
            {self._plan_select}
            {where}
            GROUP BY sp.id
        """), {"plan_id": plan_id})
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
            text("""
                SELECT s.*, sp.duration_months, sp.name AS plan_name
                FROM subscriptions s
                LEFT JOIN subscription_plans sp ON sp.id = s.plan_id
                WHERE s.razorpay_order_id = :oid
            """),
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
        subs = await self.get_active_subscriptions(db, parent_id)
        return subs[0] if subs else None

    async def get_active_subscriptions(self, db: AsyncSession, parent_id: UUID) -> list[dict]:
        result = await db.execute(
            text("""
                SELECT s.*, sp.name as plan_name
                FROM subscriptions s
                LEFT JOIN subscription_plans sp ON sp.id = s.plan_id
                WHERE s.parent_id = :pid AND s.status = 'active' AND s.expires_at > now()
                ORDER BY s.expires_at DESC
            """),
            {"pid": str(parent_id)},
        )
        return [dict(row) for row in result.mappings().all()]

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

    async def create_plan(self, db: AsyncSession, data: dict) -> dict:
        result = await db.execute(text("""
            INSERT INTO subscription_plans
                (name, duration_months, price_inr, features, description_en,
                 description_mr, display_order, is_active)
            VALUES
                (:name, :duration_months, :price_inr, CAST(:features AS jsonb),
                 :description_en, :description_mr, :display_order, true)
            RETURNING id
        """), {
            "name": data["name"],
            "duration_months": data["duration_months"],
            "price_inr": data["price_inr"],
            "features": data.get("features_json", "{}"),
            "description_en": data.get("description_en"),
            "description_mr": data.get("description_mr"),
            "display_order": data.get("display_order", 1),
        })
        plan_id = result.scalar_one()
        return await self.get_plan_by_id(db, plan_id)

    async def update_plan(self, db: AsyncSession, plan_id: int, data: dict) -> dict | None:
        if not data:
            return await self.get_plan_by_id(db, plan_id)
        assignments = []
        params = {"plan_id": plan_id}
        for key, value in data.items():
            if key == "features_json":
                assignments.append("features = CAST(:features_json AS jsonb)")
            else:
                assignments.append(f"{key} = :{key}")
            params[key] = value
        await db.execute(text(f"""
            UPDATE subscription_plans
            SET {", ".join(assignments)}
            WHERE id = :plan_id
        """), params)
        return await self.get_plan_by_id(db, plan_id)

    async def add_plan_entitlement(self, db: AsyncSession, plan_id: int, data: dict) -> dict:
        result = await db.execute(text("""
            INSERT INTO subscription_plan_entitlements
                (plan_id, scope_type, board_id, category_id, std_class, event_id, exam_id)
            VALUES
                (:plan_id, :scope_type, :board_id, :category_id, :std_class, :event_id, :exam_id)
            RETURNING id, scope_type, board_id, category_id, std_class, event_id, exam_id
        """), {
            "plan_id": plan_id,
            "scope_type": data["scope_type"],
            "board_id": data.get("board_id"),
            "category_id": data.get("category_id"),
            "std_class": data.get("std_class"),
            "event_id": data.get("event_id"),
            "exam_id": data.get("exam_id"),
        })
        return dict(result.mappings().first())

    async def delete_plan_entitlement(
        self, db: AsyncSession, plan_id: int, entitlement_id: int
    ) -> bool:
        result = await db.execute(text("""
            DELETE FROM subscription_plan_entitlements
            WHERE id = :entitlement_id AND plan_id = :plan_id
        """), {"entitlement_id": entitlement_id, "plan_id": plan_id})
        return result.rowcount > 0

    async def get_plan_scope_options(self, db: AsyncSession) -> dict:
        result = await db.execute(text("""
            SELECT
                COALESCE((SELECT jsonb_agg(jsonb_build_object('id', id, 'name_en', name_en, 'short_code', short_code) ORDER BY name_en)
                          FROM exam_boards), '[]'::jsonb) AS boards,
                COALESCE((SELECT jsonb_agg(jsonb_build_object('id', ec.id, 'board_id', ec.board_id, 'name_en', ec.name_en) ORDER BY ec.name_en)
                          FROM exam_categories ec), '[]'::jsonb) AS categories,
                COALESCE((SELECT jsonb_agg(jsonb_build_object('id', ee.id, 'board_id', ee.board_id, 'category_id', ee.category_id,
                                                             'title_en', ee.title_en, 'std_class', ee.std_class, 'year', ee.year)
                                      ORDER BY ee.year DESC, ee.title_en)
                          FROM exam_events ee), '[]'::jsonb) AS events,
                COALESCE((SELECT jsonb_agg(jsonb_build_object('id', e.id, 'event_id', e.event_id, 'title_en', e.title_en,
                                                             'paper_code', e.paper_code, 'set_code', e.set_code)
                                      ORDER BY e.id DESC)
                          FROM exams e), '[]'::jsonb) AS exams
        """))
        row = result.mappings().first()
        return dict(row) if row else {"boards": [], "categories": [], "events": [], "exams": []}

    async def get_all_subscriptions_admin(
        self, db: AsyncSession, page: int = 1, limit: int = 50
    ) -> list[dict]:
        result = await db.execute(text("""
            SELECT
                s.id,
                up.id AS parent_id,
                up.full_name AS parent_name,
                au.email AS parent_email,
                sp.name AS plan_name,
                CASE
                    WHEN s.id IS NULL THEN 'free'
                    WHEN s.status = 'active' AND s.expires_at <= now() THEN 'expired'
                    ELSE s.status
                END AS status,
                s.amount_paid_inr,
                s.started_at,
                s.expires_at,
                COALESCE(s.created_at, up.created_at) AS created_at
            FROM user_profiles up
            LEFT JOIN auth.users au ON au.id = up.id
            LEFT JOIN LATERAL (
                SELECT *
                FROM subscriptions s
                WHERE s.parent_id = up.id
                ORDER BY
                    CASE
                        WHEN s.status = 'active' AND s.expires_at > now() THEN 0
                        WHEN s.status = 'pending' THEN 1
                        ELSE 2
                    END,
                    s.created_at DESC
                LIMIT 1
            ) s ON true
            LEFT JOIN subscription_plans sp ON sp.id = s.plan_id
            WHERE up.role = 'parent'
              AND up.is_active = true
            ORDER BY
                CASE
                    WHEN s.id IS NULL THEN 1
                    ELSE 0
                END,
                COALESCE(s.created_at, up.created_at) DESC
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
                (SELECT COUNT(*) FROM user_profiles WHERE role = 'parent' AND is_active = true)
                    AS total_parent_users,
                (
                    SELECT COUNT(*)
                    FROM user_profiles up
                    WHERE up.role = 'parent'
                      AND up.is_active = true
                      AND NOT EXISTS (
                          SELECT 1
                          FROM subscriptions s2
                          WHERE s2.parent_id = up.id
                            AND s2.status = 'active'
                            AND s2.expires_at > now()
                      )
                )                                                               AS free_parent_users,
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
