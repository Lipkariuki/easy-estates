from typing import Any, List, Sequence

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str
    JWT_SECRET: str = "change-this"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: List[str] | str = ["http://localhost:5173"]
    PROJECT_NAME: str = "Easy Estates"
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_BUCKET: str | None = None
    S3_REGION: str | None = None
    SENDGRID_API_KEY: str | None = None
    SENDGRID_FROM_EMAIL: str | None = None
    SUPPORT_EMAIL: str | None = None
    EMIT_DEBUG_TOKENS: bool = False
    ALLOW_OPEN_TENANT_CREATION: bool = False
    ALLOW_OPEN_PROPERTY_MANAGEMENT: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, raw: Any) -> Sequence[str] | Any:
        """Normalise origins from JSON arrays, comma lists, or single strings."""
        if isinstance(raw, list):
            return raw

        if isinstance(raw, str):
            value = raw.strip()
            if not value:
                return []

            if value.startswith("[") and value.endswith("]"):
                import json

                return json.loads(value)

            if "," in value:
                return [origin.strip() for origin in value.split(",") if origin.strip()]

            return [value]

        return raw

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def jwt_secret(self) -> str:
        return self.JWT_SECRET

    @property
    def jwt_algorithm(self) -> str:
        return self.JWT_ALGORITHM

    @property
    def access_token_exp_minutes(self) -> int:
        return self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def cors_origins(self) -> List[str]:
        value = self.CORS_ORIGINS
        return value if isinstance(value, list) else [value]

    @property
    def project_name(self) -> str:
        return self.PROJECT_NAME

    @property
    def frontend_base_url(self) -> str:
        return self.FRONTEND_BASE_URL

    @property
    def s3_access_key_id(self) -> str | None:
        return self.S3_ACCESS_KEY_ID

    @property
    def s3_secret_access_key(self) -> str | None:
        return self.S3_SECRET_ACCESS_KEY

    @property
    def s3_bucket(self) -> str | None:
        return self.S3_BUCKET

    @property
    def s3_region(self) -> str | None:
        return self.S3_REGION

    @property
    def sendgrid_api_key(self) -> str | None:
        return self.SENDGRID_API_KEY

    @property
    def sendgrid_from_email(self) -> str | None:
        return self.SENDGRID_FROM_EMAIL

    @property
    def support_email(self) -> str | None:
        return self.SUPPORT_EMAIL

    @property
    def emit_debug_tokens(self) -> bool:
        return self.EMIT_DEBUG_TOKENS

    @property
    def allow_open_tenant_creation(self) -> bool:
        return self.ALLOW_OPEN_TENANT_CREATION

    @property
    def allow_open_property_management(self) -> bool:
        return self.ALLOW_OPEN_PROPERTY_MANAGEMENT


settings = Settings()
