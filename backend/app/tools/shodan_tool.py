"""Shodan Tool — search for open ports, services, and banners.

Uses the Shodan API to find publicly exposed services.
Rate limit: 1 req/sec, API key required.
"""

import asyncio
import logging
from typing import Any

from app.config import settings
from app.tools.base_tool import BaseTool

logger = logging.getLogger("cyberscore.tools.shodan")


class ShodanTool(BaseTool):
    """Shodan API integration for network reconnaissance."""

    def __init__(self) -> None:
        super().__init__(
            name="shodan",
            base_url="https://api.shodan.io",
            api_key=settings.shodan_api_key,
            timeout=30.0,
        )
        self.headers = {"Accept": "application/json"}

    async def resolve_domain(self, domain: str) -> dict[str, str]:
        """Resolve domain to IP addresses via Shodan DNS.

        Args:
            domain: Target domain name.

        Returns:
            Dict mapping hostname to IP address.
        """
        result = await self._request(
            "GET",
            "/dns/resolve",
            params={"hostnames": domain, "key": self._api_key},
        )
        return result

    async def host_info(self, ip: str) -> dict[str, Any]:
        """Get detailed info about a specific IP.

        Args:
            ip: IP address to look up.

        Returns:
            Dict with ports, services, banners, vulns.
        """
        result = await self._request(
            "GET",
            f"/shodan/host/{ip}",
            params={"key": self._api_key},
        )
        return {
            "ip": ip,
            "source": "shodan",
            "data": result,
        }

    async def search(self, domain: str) -> dict[str, Any]:
        """Search Shodan for hosts associated with a domain.

        Resolves the domain to IPs, then fetches host details for each.

        Args:
            domain: Target domain name.

        Returns:
            Dict with open ports, services, banners, and vulnerabilities.
        """
        # Step 1: Resolve domain to IPs
        try:
            dns_result = await self.resolve_domain(domain)
        except Exception as exc:
            logger.warning("Shodan DNS resolve failed for %s: %s", domain, exc)
            return {
                "domain": domain,
                "source": "shodan",
                "ips": [],
                "hosts": [],
                "open_ports": [],
            }

        ip = dns_result.get(domain)
        if not ip:
            return {
                "domain": domain,
                "source": "shodan",
                "ips": [],
                "hosts": [],
                "open_ports": [],
            }

        # Step 2: Get host info for the resolved IP
        # Rate limit: wait 1s between calls
        await asyncio.sleep(1.0)
        try:
            host_data = await self.host_info(ip)
        except Exception as exc:
            logger.warning("Shodan host info failed for %s: %s", ip, exc)
            return {
                "domain": domain,
                "source": "shodan",
                "ips": [ip],
                "hosts": [],
                "open_ports": [],
            }

        raw = host_data.get("data", {})
        ports = raw.get("ports", [])
        services = raw.get("data", [])

        open_ports = []
        for svc in services if isinstance(services, list) else []:
            open_ports.append({
                "port": svc.get("port"),
                "transport": svc.get("transport", "tcp"),
                "service": svc.get("product", svc.get("_shodan", {}).get("module", "unknown")),
                "version": svc.get("version", ""),
                "banner": (svc.get("data", "") or "")[:200],
                "tls": "ssl" in svc,
                "vulns": list(svc.get("vulns", {}).keys()) if svc.get("vulns") else [],
            })

        return {
            "domain": domain,
            "source": "shodan",
            "ips": [ip],
            "hosts": [raw],
            "open_ports": open_ports,
            "port_numbers": ports,
            "vulns": raw.get("vulns", []),
            "os": raw.get("os"),
            "isp": raw.get("isp"),
            "org": raw.get("org"),
            "country_code": raw.get("country_code"),
        }
