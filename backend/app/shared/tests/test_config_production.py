import pytest
from pydantic import ValidationError

from app.config import Settings


def _production_settings(**overrides):
    values = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@example.com/postgres",
        "SECRET_KEY": "x" * 32,
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_JWT_SECRET": "jwt-secret",
        "SUPABASE_SERVICE_KEY": "service-key",
        "FRONTEND_URL": "https://scholarpath.example.com",
        "DEBUG": False,
        "MEDIA_PROVIDER": "local",
        "RAZORPAY_KEY_ID": "rzp_live_public",
        "RAZORPAY_KEY_SECRET": "razorpay-secret",
        "RAZORPAY_WEBHOOK_SECRET": "webhook-secret",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_production_requires_razorpay_secrets():
    with pytest.raises(ValidationError, match="RAZORPAY_KEY_SECRET"):
        _production_settings(RAZORPAY_KEY_SECRET="")


def test_production_rejects_localhost_frontend_url():
    with pytest.raises(ValidationError, match="FRONTEND_URL"):
        _production_settings(FRONTEND_URL="http://localhost:5173")


def test_production_accepts_complete_required_settings():
    settings = _production_settings()

    assert settings.DEBUG is False
    assert settings.RAZORPAY_WEBHOOK_SECRET == "webhook-secret"
