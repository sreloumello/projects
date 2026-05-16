# app/config.py — centralized configuration via environment variables

import os
import boto3
from functools import lru_cache


class Settings:
    ENV:                    str = os.getenv("ENV", "dev")
    DB_HOST:                str = os.getenv("DB_HOST", "localhost")
    DB_PORT:                int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME:                str = os.getenv("DB_NAME", "kanbandb")
    DB_USER:                str = os.getenv("DB_USER", "dbadmin")
    DB_PASSWORD_SECRET_ARN: str = os.getenv("DB_PASSWORD_SECRET_ARN", "")
    DB_PASSWORD:            str = os.getenv("DB_PASSWORD", "localpassword")

    COGNITO_USER_POOL_ID: str = os.getenv("COGNITO_USER_POOL_ID", "")
    COGNITO_CLIENT_ID:    str = os.getenv("COGNITO_CLIENT_ID", "")
    COGNITO_REGION:       str = os.getenv("COGNITO_REGION", "us-east-1")

    ALLOWED_ORIGIN: str = os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")

    # cookie is secure only in non-dev environments
    COOKIE_SECURE:   bool = ENV != "dev"
    COOKIE_SAMESITE: str  = "none" if ENV != "dev" else "lax"

    @property
    def db_password(self) -> str:
        # in production, fetch password from secrets manager
        if self.DB_PASSWORD_SECRET_ARN:
            client = boto3.client(
                "secretsmanager",
                region_name=self.COGNITO_REGION,
                endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
            )
            return client.get_secret_value(
                SecretId=self.DB_PASSWORD_SECRET_ARN
            )["SecretString"]
        return self.DB_PASSWORD

    @property
    def cognito_jwks_url(self) -> str:
        base = os.getenv("AWS_ENDPOINT_URL", "https://cognito-idp.amazonaws.com")
        if self.ENV == "dev":
            return f"{base}/{self.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        return (
            f"https://cognito-idp.{self.COGNITO_REGION}.amazonaws.com"
            f"/{self.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
