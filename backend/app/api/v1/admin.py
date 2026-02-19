"""Admin endpoints: scoring weights, user management, system config, LLM config."""

import base64
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.config import settings
from app.models.llm_config import LLMConfig
from app.models.user import User
from app.schemas.llm_config import (
    LLM_PROVIDERS,
    LLMConfigCreate,
    LLMConfigResponse,
    LLMConfigTestResponse,
    LLMProviderInfo,
)
from app.services.llm_provider import LLMProviderConfig, get_llm_provider
from app.utils.constants import DEFAULT_DOMAIN_WEIGHTS, SCORING_DOMAINS
from app.utils.crypto import decrypt_data, encrypt_data

logger = logging.getLogger("mh_cyberscore.admin")

router = APIRouter(prefix="/admin", tags=["admin"])

# In-memory scoring weights (in production, persist to DB or config store)
_scoring_weights: dict[str, float] = dict(DEFAULT_DOMAIN_WEIGHTS)


class ScoringWeightsResponse(BaseModel):
    """Current scoring weights with domain metadata."""

    weights: dict[str, float]
    domains: dict[str, str]


class ScoringWeightsUpdate(BaseModel):
    """Request to update scoring weights."""

    weights: dict[str, float] = Field(
        ..., description="Map of domain ID (D1-D8) to weight (0.0-1.0)"
    )


@router.get("/scoring-weights", response_model=ScoringWeightsResponse)
async def get_scoring_weights(
    _current_user: object = Depends(require_role("admin", "rssi")),
) -> ScoringWeightsResponse:
    """Get current scoring domain weights."""
    return ScoringWeightsResponse(
        weights=_scoring_weights,
        domains=SCORING_DOMAINS,
    )


@router.put("/scoring-weights", response_model=ScoringWeightsResponse)
async def update_scoring_weights(
    body: ScoringWeightsUpdate,
    _current_user: object = Depends(require_role("admin")),
) -> ScoringWeightsResponse:
    """Update scoring domain weights (admin only).

    Weights should sum to approximately 1.0.
    """
    for key, value in body.weights.items():
        if key in _scoring_weights:
            _scoring_weights[key] = value
    return ScoringWeightsResponse(
        weights=_scoring_weights,
        domains=SCORING_DOMAINS,
    )


@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin", "rssi")),
) -> list[dict]:
    """List all application users."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "keycloak_id": u.keycloak_id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.get("/config")
async def get_system_config(
    _current_user: object = Depends(require_role("admin")),
) -> dict:
    """Get non-sensitive system configuration."""
    return {
        "debug": settings.debug,
        "keycloak_realm": settings.keycloak_realm,
        "llm_model": settings.llm_model,
        "cors_origins": settings.cors_origins,
        "scoring_domains": SCORING_DOMAINS,
        "scoring_weights": _scoring_weights,
    }


# ---------------------------------------------------------------------------
# LLM Configuration Endpoints
# ---------------------------------------------------------------------------


def _get_encryption_key() -> bytes:
    """Load the AES-256 encryption key from settings."""
    if not settings.encryption_key:
        raise HTTPException(
            status_code=500,
            detail="MH_ENCRYPTION_KEY not configured on server",
        )
    return base64.b64decode(settings.encryption_key)


def _mask_api_key(encrypted_key: str | None, enc_key: bytes) -> str | None:
    """Decrypt then mask an API key for display."""
    if not encrypted_key:
        return None
    try:
        plaintext = decrypt_data(encrypted_key, enc_key)
    except Exception:
        return "****"
    if len(plaintext) <= 8:
        return "****"
    return f"{plaintext[:4]}****{plaintext[-4:]}"


def _llm_config_to_response(
    cfg: LLMConfig, enc_key: bytes
) -> LLMConfigResponse:
    """Convert a DB config row to a response with masked key."""
    return LLMConfigResponse(
        id=cfg.id,
        provider=cfg.provider,
        model_name=cfg.model_name,
        api_key_masked=_mask_api_key(cfg.api_key_encrypted, enc_key),
        api_base_url=cfg.api_base_url,
        is_active=cfg.is_active,
    )


@router.get("/llm-config", response_model=LLMConfigResponse | None)
async def get_llm_config(
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin")),
) -> LLMConfigResponse | None:
    """Get the current active LLM configuration (API key masked)."""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.is_active.is_(True)).limit(1)
    )
    cfg = result.scalar_one_or_none()
    if cfg is None:
        return None
    enc_key = _get_encryption_key()
    return _llm_config_to_response(cfg, enc_key)


@router.put("/llm-config", response_model=LLMConfigResponse)
async def update_llm_config(
    body: LLMConfigCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin")),
) -> LLMConfigResponse:
    """Create or update the active LLM configuration.

    Deactivates any existing active config and sets the new one as active.
    """
    enc_key = _get_encryption_key()

    # Deactivate all existing active configs
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.is_active.is_(True))
    )
    for existing in result.scalars().all():
        existing.is_active = False

    # Encrypt API key if provided
    encrypted_key = None
    if body.api_key:
        encrypted_key = encrypt_data(body.api_key, enc_key)

    new_config = LLMConfig(
        provider=body.provider,
        model_name=body.model_name,
        api_key_encrypted=encrypted_key,
        api_base_url=body.api_base_url,
        is_active=True,
    )
    db.add(new_config)
    await db.flush()
    return _llm_config_to_response(new_config, enc_key)


@router.post("/llm-config/test", response_model=LLMConfigTestResponse)
async def test_llm_config(
    body: LLMConfigCreate,
    _current_user: object = Depends(require_role("admin")),
) -> LLMConfigTestResponse:
    """Test an LLM provider connection without saving the config."""
    provider_config = LLMProviderConfig(
        provider=body.provider,
        model_name=body.model_name,
        api_key=body.api_key,
        api_base_url=body.api_base_url,
    )
    try:
        provider = get_llm_provider(provider_config)
        response = await provider.chat(
            messages=[{"role": "user", "content": "Say 'connection OK' in one sentence."}],
            temperature=0.0,
            max_tokens=50,
        )
        return LLMConfigTestResponse(
            success=True,
            message="Connection successful",
            response_preview=response[:200],
        )
    except Exception as exc:
        logger.warning("LLM connection test failed: %s", exc)
        return LLMConfigTestResponse(
            success=False,
            message=f"Connection failed: {exc}",
        )


@router.get("/llm-providers", response_model=list[LLMProviderInfo])
async def list_llm_providers(
    _current_user: object = Depends(require_role("admin")),
) -> list[LLMProviderInfo]:
    """List all available LLM providers with their supported models."""
    return LLM_PROVIDERS
