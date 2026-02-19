"""Censys Tool — search for certificates, services, and hosts.

Uses the Censys Search API for certificate and service discovery.
"""

from typing import Any

from app.config import settings
from app.tools.base_tool import BaseTool


class CensysTool(BaseTool):
    """Censys API integration for certificate and service discovery."""

    def __init__(self) -> None:
        super().__init__(
            name="censys",
            base_url="https://search.censys.io/api",
            timeout=30.0,
        )
        import base64

        credentials = base64.b64encode(
            f"{settings.censys_api_id}:{settings.censys_api_secret}".encode()
        ).decode()
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {credentials}",
        }

    async def search_hosts(self, domain: str) -> dict[str, Any]:
        """Search Censys for hosts associated with a domain.

        Args:
            domain: Target domain.

        Returns:
            Dict with host data (services, ports, certificates).
        """
        result = await self._request(
            "GET",
            "/v2/hosts/search",
            params={"q": domain, "per_page": 25},
        )
        return {"domain": domain, "source": "censys", "data": result}

    async def search_certificates(self, domain: str) -> dict[str, Any]:
        """Search for certificates issued for a domain.

        Args:
            domain: Target domain.

        Returns:
            Dict with certificate data.
        """
        result = await self._request(
            "GET",
            "/v2/certificates/search",
            params={"q": f"names:{domain}", "per_page": 25},
        )
        return {"domain": domain, "source": "censys_certs", "data": result}
