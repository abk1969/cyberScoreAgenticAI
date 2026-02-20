"""Base agent class for all CyberScore AI agents.

Provides rate limiting, timeout, retry with exponential backoff,
structured logging, audit trail for every external API call, and
LLM provider integration.
"""

import asyncio
import base64
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.utils.exceptions import AgentError

logger = logging.getLogger("cyberscore.agents")


@dataclass
class AgentResult:
    """Result container for agent execution."""

    agent_name: str
    vendor_id: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    api_calls_made: int = 0


class BaseAgent(ABC):
    """Abstract base class for all CyberScore agents.

    Provides:
        - Rate limiting: 1 request/sec per external API
        - Timeout: 30s per request (configurable)
        - Retry: 3x with exponential backoff
        - Structured logging with agent name and task ID
        - Audit trail for every external API call
    """

    def __init__(
        self,
        name: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit_per_sec: float = 1.0,
    ) -> None:
        self.name = name
        self.timeout = timeout
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(int(rate_limit_per_sec))
        self._api_call_count = 0
        self._audit_log: list[dict[str, Any]] = []
        self.logger = logging.getLogger(f"cyberscore.agents.{name}")

    @abstractmethod
    async def execute(self, vendor_id: str, **kwargs: Any) -> AgentResult:
        """Execute the agent's main task.

        Args:
            vendor_id: The vendor to process.
            **kwargs: Additional parameters.

        Returns:
            AgentResult with collected data or errors.
        """

    async def _rate_limited_call(
        self,
        coro: Any,
        source: str,
        **log_context: Any,
    ) -> Any:
        """Execute an async call with rate limiting, timeout, and logging.

        Args:
            coro: The coroutine to execute.
            source: Name of the external API being called.
            **log_context: Additional context for audit logging.

        Returns:
            Result of the coroutine.

        Raises:
            AgentError: If all retries fail or timeout occurs.
        """
        async with self._semaphore:
            start = time.monotonic()
            try:
                result = await asyncio.wait_for(coro, timeout=self.timeout)
                duration = time.monotonic() - start
                self._log_api_call(source, "success", duration, **log_context)
                return result
            except asyncio.TimeoutError:
                duration = time.monotonic() - start
                self._log_api_call(source, "timeout", duration, **log_context)
                raise AgentError(
                    f"[{self.name}] Timeout after {self.timeout}s calling {source}"
                )
            except Exception as exc:
                duration = time.monotonic() - start
                self._log_api_call(
                    source, "error", duration, error=str(exc), **log_context
                )
                raise AgentError(
                    f"[{self.name}] Error calling {source}: {exc}"
                ) from exc

    def _log_api_call(
        self,
        source: str,
        status: str,
        duration: float,
        **context: Any,
    ) -> None:
        """Log an external API call for audit trail.

        Args:
            source: API name.
            status: success, timeout, error.
            duration: Call duration in seconds.
            **context: Additional context.
        """
        self._api_call_count += 1
        entry = {
            "agent": self.name,
            "source": source,
            "status": status,
            "duration_seconds": round(duration, 3),
            "timestamp": time.time(),
            **context,
        }
        self._audit_log.append(entry)
        self.logger.info(
            "API call: %s → %s (%.3fs)",
            source,
            status,
            duration,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(AgentError),
        reraise=True,
    )
    async def _call_with_retry(self, coro: Any, source: str) -> Any:
        """Call with retry and exponential backoff.

        Args:
            coro: Coroutine to execute.
            source: API source name for logging.

        Returns:
            Result of the coroutine.
        """
        return await self._rate_limited_call(coro, source)

    def get_audit_log(self) -> list[dict[str, Any]]:
        """Return the audit log of all API calls made."""
        return self._audit_log.copy()

    async def _get_llm_provider(self) -> "BaseLLMProvider":  # noqa: F821
        """Load the active LLM config from DB and return a provider instance.

        Falls back to settings defaults if no active DB config exists.
        """
        from app.config import settings
        from app.database import async_session
        from app.models.llm_config import LLMConfig
        from app.services.llm_provider import (
            BaseLLMProvider,
            LLMProviderConfig,
            get_llm_provider,
        )
        from app.utils.crypto import decrypt_data

        from sqlalchemy import select

        async with async_session() as session:
            result = await session.execute(
                select(LLMConfig).where(LLMConfig.is_active.is_(True)).limit(1)
            )
            cfg = result.scalar_one_or_none()

        if cfg is not None:
            api_key = None
            if cfg.api_key_encrypted and settings.encryption_key:
                enc_key = base64.b64decode(settings.encryption_key)
                api_key = decrypt_data(cfg.api_key_encrypted, enc_key)
            return get_llm_provider(
                LLMProviderConfig(
                    provider=cfg.provider,
                    model_name=cfg.model_name,
                    api_key=api_key,
                    api_base_url=cfg.api_base_url,
                )
            )

        # Fallback: use settings defaults
        return get_llm_provider(
            LLMProviderConfig(
                provider=settings.llm_default_provider,
                model_name=settings.llm_default_model,
                api_base_url=(
                    settings.ollama_base_url
                    if settings.llm_default_provider == "ollama"
                    else None
                ),
            )
        )
