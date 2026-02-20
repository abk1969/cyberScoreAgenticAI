"""CVE Tool — search for known vulnerabilities via NVD and EUVD APIs.

Uses the NIST NVD API (public, no US dependency for data access)
and the ENISA EUVD (European Vulnerability Database).
"""

import logging
from typing import Any

from app.tools.base_tool import BaseTool

logger = logging.getLogger("cyberscore.tools.cve")


class CVETool(BaseTool):
    """CVE vulnerability search via NVD and EUVD."""

    def __init__(self) -> None:
        super().__init__(
            name="cve",
            base_url="https://services.nvd.nist.gov/rest/json",
            timeout=30.0,
        )
        self.headers = {"Accept": "application/json"}

    async def search_by_cpe(self, cpe: str) -> dict[str, Any]:
        """Search CVEs matching a CPE string.

        Args:
            cpe: CPE 2.3 string (e.g., cpe:2.3:a:apache:httpd:2.4.49:*).

        Returns:
            Dict with matching CVEs, CVSS scores, and descriptions.
        """
        result = await self._request(
            "GET",
            "/cves/2.0",
            params={"cpeName": cpe, "resultsPerPage": 20},
        )
        return {"cpe": cpe, "source": "nvd", "data": result}

    async def search_by_keyword(self, keyword: str) -> dict[str, Any]:
        """Search CVEs by keyword.

        Args:
            keyword: Search keyword (product name, vendor).

        Returns:
            Dict with matching CVEs.
        """
        result = await self._request(
            "GET",
            "/cves/2.0",
            params={"keywordSearch": keyword, "resultsPerPage": 20},
        )
        return {"keyword": keyword, "source": "nvd", "data": result}

    async def get_cve(self, cve_id: str) -> dict[str, Any]:
        """Get details of a specific CVE.

        Args:
            cve_id: CVE identifier (e.g., CVE-2024-12345).

        Returns:
            Dict with CVE details, CVSS, references.
        """
        result = await self._request(
            "GET",
            "/cves/2.0",
            params={"cveId": cve_id},
        )
        return {"cve_id": cve_id, "source": "nvd", "data": result}
