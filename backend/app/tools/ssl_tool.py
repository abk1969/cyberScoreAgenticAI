"""SSL/TLS Tool — check TLS configuration and certificate details.

Connects to the target domain to verify TLS version, cipher suites,
certificate chain, and expiration date. Also fetches HTTP security headers.
"""

import logging
import ssl
import socket
from datetime import datetime, timezone
from typing import Any

import httpx

from app.services.proxy_service import get_scan_http_client
from app.tools.base_tool import BaseTool

logger = logging.getLogger("mh_cyberscore.tools.ssl")


class SSLTool(BaseTool):
    """TLS/SSL certificate and configuration checker."""

    def __init__(self) -> None:
        super().__init__(name="ssl", base_url="", timeout=10.0)

    async def check(self, domain: str, port: int = 443) -> dict[str, Any]:
        """Check TLS configuration for a domain.

        Args:
            domain: Target domain.
            port: HTTPS port (default 443).

        Returns:
            Dict with TLS version, cipher, cert details, grade.
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection(
                (domain, port), timeout=self.timeout
            ) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()

                    not_after = datetime.strptime(
                        cert.get("notAfter", ""),
                        "%b %d %H:%M:%S %Y %Z",
                    ).replace(tzinfo=timezone.utc)
                    days_until_expiry = (
                        not_after - datetime.now(timezone.utc)
                    ).days

                    return {
                        "domain": domain,
                        "source": "ssl_check",
                        "tls_version": version,
                        "cipher_suite": cipher[0] if cipher else None,
                        "cipher_bits": cipher[2] if cipher else None,
                        "subject": dict(x[0] for x in cert.get("subject", ())),
                        "issuer": dict(x[0] for x in cert.get("issuer", ())),
                        "not_before": cert.get("notBefore"),
                        "not_after": cert.get("notAfter"),
                        "days_until_expiry": days_until_expiry,
                        "san": [
                            entry[1]
                            for entry in cert.get("subjectAltName", ())
                        ],
                        "grade": self._calculate_grade(version, days_until_expiry),
                    }
        except Exception as exc:
            logger.warning("SSL check failed for %s: %s", domain, exc)
            return {
                "domain": domain,
                "source": "ssl_check",
                "error": str(exc),
                "grade": "F",
            }

    async def check_http_headers(self, domain: str) -> dict[str, str]:
        """Fetch HTTP response headers for security analysis.

        Makes a passive GET request to https://domain and returns
        the response headers (security-relevant ones).

        Args:
            domain: Target domain.

        Returns:
            Dict of HTTP response header names to values.
        """
        url = f"https://{domain}"
        try:
            async with get_scan_http_client(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=3,
            ) as client:
                response = await client.get(url)
                return dict(response.headers)
        except Exception as exc:
            logger.warning("HTTP header check failed for %s: %s", domain, exc)
            return {}

    @staticmethod
    def _calculate_grade(tls_version: str | None, days_expiry: int) -> str:
        """Calculate a simple TLS grade.

        Args:
            tls_version: TLS version string.
            days_expiry: Days until certificate expiration.

        Returns:
            Grade A-F.
        """
        if tls_version == "TLSv1.3" and days_expiry > 30:
            return "A"
        if tls_version == "TLSv1.3" and days_expiry > 7:
            return "B"
        if tls_version == "TLSv1.2" and days_expiry > 30:
            return "B"
        if tls_version == "TLSv1.2":
            return "C"
        if tls_version in ("TLSv1.1", "TLSv1"):
            return "D"
        return "F"
