"""HIBP Tool — Have I Been Pwned API for breach detection.

Checks if a domain has been involved in known data breaches.
Requires an HIBP API key (paid tier for domain searches).
"""

import logging
from typing import Any

from app.config import settings
from app.tools.base_tool import BaseTool

logger = logging.getLogger("cyberscore.tools.hibp")


class HIBPTool(BaseTool):
    """Have I Been Pwned API integration."""

    def __init__(self) -> None:
        super().__init__(
            name="hibp",
            base_url="https://haveibeenpwned.com/api/v3",
            api_key=settings.hibp_api_key,
            timeout=15.0,
        )
        self.headers = {
            "hibp-api-key": self._api_key,
            "User-Agent": "CyberScore-VRM",
            "Accept": "application/json",
        }

    async def check_breaches(self, domain: str) -> dict[str, Any]:
        """Check breaches associated with a domain.

        Args:
            domain: Target domain.

        Returns:
            Dict with breach list (name, date, count, data classes).
        """
        try:
            result = await self._request(
                "GET",
                "/breaches",
                params={"domain": domain},
            )
            breaches = result if isinstance(result, list) else []
            return {
                "domain": domain,
                "source": "hibp",
                "breach_count": len(breaches),
                "breaches": breaches,
            }
        except Exception:
            return {
                "domain": domain,
                "source": "hibp",
                "breach_count": 0,
                "breaches": [],
            }

    async def check_pastes(self, email: str) -> dict[str, Any]:
        """Check paste sites for an email (requires enterprise key).

        Args:
            email: Email address to check.

        Returns:
            Dict with paste occurrences.
        """
        try:
            result = await self._request(
                "GET",
                f"/pasteaccount/{email}",
            )
            return {"email": email, "source": "hibp_pastes", "data": result}
        except Exception:
            return {"email": email, "source": "hibp_pastes", "data": []}
