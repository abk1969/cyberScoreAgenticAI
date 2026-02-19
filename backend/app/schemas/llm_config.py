"""Pydantic schemas for LLM configuration."""

from pydantic import BaseModel, Field


class LLMConfigCreate(BaseModel):
    """Request schema for creating/updating LLM configuration."""

    provider: str = Field(
        ...,
        pattern=r"^(mistral|gemini|claude|openai|ollama)$",
        description="LLM provider name",
    )
    model_name: str = Field(..., min_length=1, max_length=100)
    api_key: str | None = Field(
        None, description="API key (will be encrypted at rest)"
    )
    api_base_url: str | None = Field(
        None, description="Custom API base URL (required for Ollama)"
    )


class LLMConfigResponse(BaseModel):
    """Response schema for LLM configuration (API key masked)."""

    id: str
    provider: str
    model_name: str
    api_key_masked: str | None = Field(
        None, description="Masked API key (e.g. sk-****1234)"
    )
    api_base_url: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class LLMConfigTestResponse(BaseModel):
    """Response from connection test."""

    success: bool
    message: str
    response_preview: str | None = None


class LLMProviderInfo(BaseModel):
    """Info about an available LLM provider."""

    name: str
    display_name: str
    models: list[str]
    requires_api_key: bool
    requires_base_url: bool


LLM_PROVIDERS: list[LLMProviderInfo] = [
    LLMProviderInfo(
        name="mistral",
        display_name="Mistral AI",
        models=[
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "open-mistral-nemo",
        ],
        requires_api_key=True,
        requires_base_url=False,
    ),
    LLMProviderInfo(
        name="gemini",
        display_name="Google Gemini",
        models=[
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ],
        requires_api_key=True,
        requires_base_url=False,
    ),
    LLMProviderInfo(
        name="claude",
        display_name="Anthropic Claude",
        models=[
            "claude-sonnet-4-20250514",
            "claude-haiku-4-5-20251001",
            "claude-3-5-sonnet-20241022",
        ],
        requires_api_key=True,
        requires_base_url=False,
    ),
    LLMProviderInfo(
        name="openai",
        display_name="OpenAI GPT",
        models=[
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
        ],
        requires_api_key=True,
        requires_base_url=False,
    ),
    LLMProviderInfo(
        name="ollama",
        display_name="Ollama (Self-hosted)",
        models=[
            "llama3.1:70b",
            "llama3.1:8b",
            "mistral:7b",
            "mixtral:8x7b",
            "qwen2.5:72b",
        ],
        requires_api_key=False,
        requires_base_url=True,
    ),
]
