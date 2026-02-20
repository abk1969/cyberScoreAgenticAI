"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """CyberScore application settings.

    All values are loaded from environment variables with the CS_ prefix.
    Example: CS_DATABASE_URL, CS_REDIS_URL, etc.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CS_")

    # Core
    debug: bool = False

    # Database
    database_url: str = "postgresql+psycopg://csadmin:csadmin@localhost:5432/cyberscore"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"

    # Keycloak / Auth
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "cyberscore"
    keycloak_client_id: str = "cyberscore-api"
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

    # Proxy / IP Anonymization for OSINT scans
    # Modes: none, tor, socks5, http, rotating
    proxy_mode: str = "none"
    proxy_tor_url: str = "socks5://127.0.0.1:9050"
    proxy_socks5_url: str = ""
    proxy_http_url: str = ""
    # Comma-separated list for rotating mode: "socks5://1.2.3.4:1080,http://5.6.7.8:8080"
    proxy_rotating_list: str = ""
    # Comma-separated hosts to bypass proxy (local services auto-bypassed)
    proxy_bypass_hosts: str = ""

    # OSINT API keys
    shodan_api_key: str = ""
    censys_api_id: str = ""
    censys_api_secret: str = ""
    virustotal_api_key: str = ""
    hibp_api_key: str = ""
    abuseipdb_api_key: str = ""

    # Qdrant (Vector DB for RAG)
    qdrant_url: str = "http://localhost:6333"

    # MinIO (S3-compatible sovereign storage)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "cyberscore"

    # Splunk HEC integration
    splunk_hec_url: str = ""
    splunk_hec_token: str = ""

    # ServiceNow integration
    servicenow_instance: str = ""
    servicenow_user: str = ""
    servicenow_password: str = ""

    # Slack webhook
    slack_webhook_url: str = ""

    # Microsoft Teams webhook
    teams_webhook_url: str = ""


settings = Settings()
