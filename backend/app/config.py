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

    # ── Cloudflare R2 (ADR-007 provider) ─────────────────────
    R2_ACCOUNT_ID: str = ""          # from URL: xxx.r2.cloudflarestorage.com
    R2_ACCESS_KEY_ID: str = ""       # R2 API token key ID
    R2_SECRET_ACCESS_KEY: str = ""   # R2 API token secret
    R2_BUCKET_NAME: str = "scolarpath"
    R2_PUBLIC_URL: str = ""          # e.g. https://<id>.r2.cloudflarestorage.com/scolarpath

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
        if not self.DEBUG:
            missing = [
                name
                for name, value in {
                    "RAZORPAY_KEY_ID": self.RAZORPAY_KEY_ID,
                    "RAZORPAY_KEY_SECRET": self.RAZORPAY_KEY_SECRET,
                    "RAZORPAY_WEBHOOK_SECRET": self.RAZORPAY_WEBHOOK_SECRET,
                }.items()
                if not value
            ]

            if self.MEDIA_PROVIDER == "cloudinary" and not self.CLOUDINARY_URL:
                missing.append("CLOUDINARY_URL")
            elif self.MEDIA_PROVIDER == "r2":
                missing.extend(
                    name
                    for name, value in {
                        "R2_ACCOUNT_ID": self.R2_ACCOUNT_ID,
                        "R2_ACCESS_KEY_ID": self.R2_ACCESS_KEY_ID,
                        "R2_SECRET_ACCESS_KEY": self.R2_SECRET_ACCESS_KEY,
                        "R2_BUCKET_NAME": self.R2_BUCKET_NAME,
                        "R2_PUBLIC_URL": self.R2_PUBLIC_URL,
                    }.items()
                    if not value
                )

            if missing:
                raise ValueError(
                    "Production configuration is missing required value(s): "
                    + ", ".join(sorted(set(missing)))
                )

            if "localhost" in self.FRONTEND_URL or "127.0.0.1" in self.FRONTEND_URL:
                raise ValueError("FRONTEND_URL must be a deployed origin when DEBUG=false")
        return self


# Single shared instance — import this everywhere
settings = Settings()
