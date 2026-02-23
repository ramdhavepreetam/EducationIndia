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
    SECRET_KEY: str = "change-me-in-production-min-32-chars"
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

    # ── App ──────────────────────────────────────────────────
    DEBUG: bool = False
    APP_NAME: str = "ScholarPath"
    APP_VERSION: str = "1.0.0"


# Single shared instance — import this everywhere
settings = Settings()
