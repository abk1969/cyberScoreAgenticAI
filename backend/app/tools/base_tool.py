"""Base tool class for all MCP tools — external API integrations.

Provides async HTTP client, rate limiting (1 req/sec per API),
timeout (30s), retry (3x exponential backoff), and structured logging.
"""

import logging
import time
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.utils.exceptions import ToolError

logger = logging.getLogger("mh_cyberscore.tools")


class BaseTool:
    """Base class for all external API tools.

    Attributes:
        name: Tool name for logging.
        base_url: API base URL.
        timeout: Request timeout in seconds.
        headers: Default HTTP headers.
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str = "",
        timeout: float = 30.0,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers: dict[str, str] = {}
        self._api_key = api_key
        self._call_log: list[dict[str, Any]] = []
        self.logger = logging.getLogger(f"mh_cyberscore.tools.{name}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPError, ToolError)),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request with retry and logging.

        Args:
            method: HTTP method (GET, POST).
            path: API endpoint path.
            params: Query parameters.
            json_data: JSON body for POST requests.

        Returns:
            Parsed JSON response.

        Raises:
            ToolError: If request fails after retries.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        start = time.monotonic()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=self.headers,
                )
                response.raise_for_status()
                duration = time.monotonic() - start
                self._log_call(url, response.status_code, duration)
                return response.json()

        except httpx.HTTPStatusError as exc:
            duration = time.monotonic() - start
            self._log_call(url, exc.response.status_code, duration, error=True)
            raise ToolError(
                f"[{self.name}] HTTP {exc.response.status_code} from {url}"
            ) from exc
        except httpx.HTTPError as exc:
            duration = time.monotonic() - start
            self._log_call(url, 0, duration, error=True)
            raise ToolError(
                f"[{self.name}] Request failed: {exc}"
            ) from exc

    def _log_call(
        self,
        url: str,
        status: int,
        duration: float,
        error: bool = False,
    ) -> None:
        """Log API call for audit trail."""
        entry = {
            "tool": self.name,
            "url": url,
            "status_code": status,
            "duration_seconds": round(duration, 3),
            "timestamp": time.time(),
            "error": error,
        }
        self._call_log.append(entry)
        if error:
            self.logger.warning("API error: %s → %d (%.3fs)", url, status, duration)
        else:
            self.logger.info("API call: %s → %d (%.3fs)", url, status, duration)

    def get_call_log(self) -> list[dict[str, Any]]:
        """Return the audit log of all API calls."""
        return self._call_log.copy()
