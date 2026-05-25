from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # NeonDB PostgreSQL — async driver (asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_oDfcQNEVy7h4@ep-withered-sky-alk11h6b-pooler.c-3.eu-central-1.aws.neon.tech/neondb?ssl=require"
    # NeonDB PostgreSQL — sync driver (for Alembic/seed)
    DATABASE_URL_SYNC: str = "postgresql://neondb_owner:npg_oDfcQNEVy7h4@ep-withered-sky-alk11h6b-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require"

    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 3600
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    MODEL_PATH: str = "./ml/models"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
