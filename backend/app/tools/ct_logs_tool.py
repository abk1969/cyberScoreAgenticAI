"""Certificate Transparency Logs Tool — search CT logs for a domain.

Uses the crt.sh public API to find certificates issued for a domain.
No API key required — public service.
"""

import logging
from typing import Any

from app.tools.base_tool import BaseTool

logger = logging.getLogger("cyberscore.tools.ct_logs")


class CTLogsTool(BaseTool):
    """Certificate Transparency logs search via crt.sh."""

    def __init__(self) -> None:
        super().__init__(
            name="ct_logs",
            base_url="https://crt.sh",
            timeout=30.0,
        )
        self.headers = {"Accept": "application/json"}

    async def search(self, domain: str) -> dict[str, Any]:
        """Search CT logs for certificates issued to a domain.

        Args:
            domain: Target domain.

        Returns:
            Dict with certificate entries (issuer, dates, SAN).
        """
        try:
            result = await self._request(
                "GET",
                "/",
                params={"q": f"%.{domain}", "output": "json"},
            )
            certs = result if isinstance(result, list) else []
            return {
                "domain": domain,
                "source": "crt.sh",
                "certificate_count": len(certs),
                "certificates": certs[:50],  # Limit to 50 most recent
            }
        except Exception as exc:
            logger.warning("CT logs search failed for %s: %s", domain, exc)
            return {
                "domain": domain,
                "source": "crt.sh",
                "certificate_count": 0,
                "certificates": [],
            }
