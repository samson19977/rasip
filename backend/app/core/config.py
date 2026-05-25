from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "rasip-rwanda-agri-secret-2025"
    API_V1_PREFIX: str = "/api/v1"

    # NeonDB
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_oDfcQNEVy7h4@ep-withered-sky-alk11h6b-pooler.c-3.eu-central-1.aws.neon.tech/neondb?ssl=require"
    DATABASE_URL_SYNC: str = "postgresql://neondb_owner:npg_oDfcQNEVy7h4@ep-withered-sky-alk11h6b-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require"

    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 3600

    # Plain string — we parse it manually below
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    MODEL_PATH: str = "./ml/models"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def allowed_origins_list(self) -> list:
        """Returns ALLOWED_ORIGINS as a list, split by comma."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
