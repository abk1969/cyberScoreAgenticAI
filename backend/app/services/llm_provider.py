"""Multi-LLM provider abstraction layer.

Supports Mistral, Google Gemini, Anthropic Claude, OpenAI GPT, and Ollama.
Each provider implements a common interface for chat and embedding.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("mh_cyberscore.llm_provider")

_HTTP_TIMEOUT = 120.0


@dataclass
class LLMProviderConfig:
    """Configuration for instantiating an LLM provider."""

    provider: str
    model_name: str
    api_key: str | None = None
    api_base_url: str | None = None


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(self, config: LLMProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.

        Returns:
            The assistant's response text.
        """

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text.

        Args:
            text: Input text to embed.

        Returns:
            List of floats representing the embedding vector.
        """

    def get_model_info(self) -> dict[str, Any]:
        """Return metadata about the current provider and model."""
        return {
            "provider": self.config.provider,
            "model_name": self.config.model_name,
            "api_base_url": self.config.api_base_url,
        }


class MistralProvider(BaseLLMProvider):
    """Mistral AI provider via their HTTP API."""

    API_BASE = "https://api.mistral.ai/v1"

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        url = f"{self.API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def embed(self, text: str) -> list[float]:
        url = f"{self.API_BASE}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "mistral-embed",
            "input": [text],
        }
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["data"][0]["embedding"]


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider via the Generative Language API."""

    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        url = (
            f"{self.API_BASE}/models/{self.config.model_name}"
            f":generateContent?key={self.config.api_key}"
        )
        # Convert OpenAI-style messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def embed(self, text: str) -> list[float]:
        url = (
            f"{self.API_BASE}/models/text-embedding-004"
            f":embedContent?key={self.config.api_key}"
        )
        payload = {"content": {"parts": [{"text": text}]}}
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["embedding"]["values"]


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider via the Messages API."""

    API_BASE = "https://api.anthropic.com/v1"

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        url = f"{self.API_BASE}/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        # Claude separates system from messages
        system_text = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text += msg["content"] + "\n"
            else:
                chat_messages.append(
                    {"role": msg["role"], "content": msg["content"]}
                )
        # Ensure messages start with a user turn
        if not chat_messages or chat_messages[0]["role"] != "user":
            chat_messages.insert(0, {"role": "user", "content": "Hello."})

        payload: dict[str, Any] = {
            "model": self.config.model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": chat_messages,
        }
        if system_text.strip():
            payload["system"] = system_text.strip()

        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["content"][0]["text"]

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError(
            "Anthropic Claude does not provide an embedding API. "
            "Use a different provider for embeddings."
        )


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider via the Chat Completions API."""

    API_BASE = "https://api.openai.com/v1"

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        url = f"{self.API_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def embed(self, text: str) -> list[float]:
        url = f"{self.API_BASE}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "text-embedding-3-small",
            "input": text,
        }
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return data["data"][0]["embedding"]


class OllamaProvider(BaseLLMProvider):
    """Ollama provider for self-hosted models."""

    def __init__(self, config: LLMProviderConfig) -> None:
        super().__init__(config)
        self.base_url = (
            config.api_base_url or "http://localhost:11434"
        ).rstrip("/")

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["message"]["content"]

    async def embed(self, text: str) -> list[float]:
        url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.config.model_name,
            "input": text,
        }
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["embeddings"][0]


_PROVIDER_MAP: dict[str, type[BaseLLMProvider]] = {
    "mistral": MistralProvider,
    "gemini": GeminiProvider,
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def get_llm_provider(config: LLMProviderConfig) -> BaseLLMProvider:
    """Factory function: instantiate the correct LLM provider.

    Args:
        config: Provider configuration.

    Returns:
        An instance of the appropriate BaseLLMProvider subclass.

    Raises:
        ValueError: If the provider name is unknown.
    """
    cls = _PROVIDER_MAP.get(config.provider)
    if cls is None:
        raise ValueError(
            f"Unknown LLM provider: {config.provider!r}. "
            f"Available: {', '.join(_PROVIDER_MAP)}"
        )
    return cls(config)
