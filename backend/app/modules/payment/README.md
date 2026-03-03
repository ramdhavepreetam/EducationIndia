# Payment Module

## Overview
Razorpay payment integration for ScholarPath (ADR-014).
One-time ₹499 payment unlocks full access for 5 months.

## Architecture
```
router.py          → HTTP endpoints
service.py         → Business logic (order/verify/activate)
webhook_handler.py → Async Razorpay event processing
repository.py      → DB operations
razorpay_client.py → SDK wrapper
models.py          → SQLAlchemy ORM models
schemas.py         → Pydantic request/response schemas
```

## Endpoints
| Method | Path                      | Auth     | Description              |
|--------|---------------------------|----------|--------------------------|
| GET    | /api/payment/plans        | Public   | Active plan + price      |
| GET    | /api/payment/status       | Parent   | Subscription status      |
| POST   | /api/payment/create-order | Parent   | Create Razorpay order    |
| POST   | /api/payment/verify       | Parent   | Verify + activate        |
| POST   | /api/payment/webhook      | None     | Razorpay webhook         |
| GET    | /api/payment/history      | Parent   | Payment records          |

## Admin Endpoints (in admin/router.py)
| Method | Path                                   | Description            |
|--------|----------------------------------------|------------------------|
| GET    | /api/admin/settings                    | All app_settings       |
| PUT    | /api/admin/settings/{key}              | Update one setting     |
| GET    | /api/admin/subscriptions               | All subscriptions      |
| POST   | /api/admin/subscriptions/{id}/extend   | Extend expiry          |

## Environment Variables
```
RAZORPAY_KEY_ID=rzp_test_xxx       # Public key
RAZORPAY_KEY_SECRET=xxx            # Private — .env only
RAZORPAY_WEBHOOK_SECRET=xxx        # Webhook — .env only
```

## Payment Flow
1. Parent → `GET /plans` → sees ₹499
2. Parent → `POST /create-order` → gets `order_id`
3. Razorpay checkout opens in browser
4. Parent pays → `POST /verify` → subscription activated
5. Razorpay → `POST /webhook` → idempotent backup activation
