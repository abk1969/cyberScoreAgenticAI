"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MH-CyberScore application settings.

    All values are loaded from environment variables with the MH_ prefix.
    Example: MH_DATABASE_URL, MH_REDIS_URL, etc.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="MH_")

    # Core
    debug: bool = False

    # Database
    database_url: str = "postgresql+psycopg://mh:mh@localhost:5432/mhcyberscore"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"

    # Keycloak / Auth
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "mh-cyberscore"
    keycloak_client_id: str = "mh-cyberscore-api"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "RS256"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # LLM (sovereign vLLM — legacy)
    vllm_url: str = "http://localhost:8000/v1"
    llm_model: str = "mistral-7b-instruct"

    # Multi-LLM provider defaults
    llm_default_provider: str = "mistral"
    llm_default_model: str = "mistral-large-latest"
    ollama_base_url: str = "http://localhost:11434"

    # Encryption key for API keys at rest (base64-encoded 32 bytes)
    encryption_key: str = ""

    # OSINT API keys
    shodan_api_key: str = ""
    censys_api_id: str = ""
    censys_api_secret: str = ""
    virustotal_api_key: str = ""
    hibp_api_key: str = ""
    abuseipdb_api_key: str = ""

    # MinIO (S3-compatible sovereign storage)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "mh-cyberscore"


settings = Settings()
