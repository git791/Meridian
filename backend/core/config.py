from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    GEMINI_API_KEY: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8080/api/v1/auth/callback"

    # Database - Using localhost for dev
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/meetings"

    # GCP
    GCP_PROJECT: str = ""
    REGION: str = "asia-southeast1"
    VERTEX_LOCATION: str = "us-central1"
    PUBSUB_TOPIC: str = "meeting-events"

    # Demo mode
    DEMO_MODE: bool = True  # Keep this True for now to bypass 401s
    DEMO_TOKEN: str = ""

    # App
    # Resilient CORS: can be JSON list string or comma-separated string
    CORS_ORIGINS: str | list[str] = [
        "http://localhost:3000", 
        "http://localhost:3005", 
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:3005"
    ]

    # SMTP (Mailhog/Mailtrap defaults)
    SMTP_HOST: str = "127.0.0.1"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "meridian@ai.example"

    # Pydantic V2 Configuration
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()