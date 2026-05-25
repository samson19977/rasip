from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "rasip-rwanda-agri-secret-2025"
    API_V1_PREFIX: str = "/api/v1"

    # NeonDB
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_oDfcQNEVy7h4@ep-withered-sky-alk11h6b-pooler.c-3.eu-central-1.aws.neon.tech/neondb?ssl=require"
    DATABASE_URL_SYNC: str = "postgresql://neondb_owner:npg_oDfcQNEVy7h4@ep-withered-sky-alk11h6b-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require"

    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 3600

    # Accepts both plain string and JSON array from Render env vars
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return ["http://localhost:3000"]
            # JSON array format: ["url1","url2"]
            if v.startswith("["):
                import json
                return json.loads(v)
            # Comma-separated: url1,url2
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    MODEL_PATH: str = "./ml/models"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
