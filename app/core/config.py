from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "changeme")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_exp_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    cors_origins: List[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
    ]
    project_name: str = os.getenv("PROJECT_NAME", "Easy Estates")
    frontend_base_url: str = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    s3_access_key_id: str | None = os.getenv("S3_ACCESS_KEY_ID")
    s3_secret_access_key: str | None = os.getenv("S3_SECRET_ACCESS_KEY")
    s3_bucket: str | None = os.getenv("S3_BUCKET")
    s3_region: str | None = os.getenv("S3_REGION")
    sendgrid_api_key: str | None = os.getenv("SENDGRID_API_KEY")
    sendgrid_from_email: str | None = os.getenv("SENDGRID_FROM_EMAIL")
    support_email: str | None = os.getenv("SUPPORT_EMAIL")
    emit_debug_tokens: bool = os.getenv("EMIT_DEBUG_TOKENS", "false").lower() in {"1", "true", "yes"}

settings = Settings()
