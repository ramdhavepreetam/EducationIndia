from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # search .env in backend/ first, then project root
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str

    # ── FastAPI JWT ──────────────────────────────────────────
    # No default — app refuses to start if SECRET_KEY is not set or is too short.
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Supabase ─────────────────────────────────────────────
    SUPABASE_URL: str
    SUPABASE_JWT_SECRET: str
    SUPABASE_SERVICE_KEY: str

    # ── Media ────────────────────────────────────────────────
    MEDIA_PROVIDER: str = "local"
    CLOUDINARY_URL: str = ""

    # ── Razorpay (ADR-014) ────────────────────────────────────
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── Frontend ─────────────────────────────────────────────
    # No default — must be set explicitly so production CORS is never localhost.
    FRONTEND_URL: str

    # ── App ──────────────────────────────────────────────────
    DEBUG: bool = False
    APP_NAME: str = "ScholarPath"
    APP_VERSION: str = "1.0.0"

    @model_validator(mode="after")
    def validate_critical_settings(self) -> "Settings":
        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return self


# Single shared instance — import this everywhere
settings = Settings()
