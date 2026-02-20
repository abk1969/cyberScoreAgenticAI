"""Reputation Tool — IP reputation checks via AbuseIPDB and VirusTotal.

Checks IP addresses against abuse databases and blacklists.
Uses separate HTTP clients per API to avoid base_url/header mutation.
"""

import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.services.proxy_service import get_scan_http_client
from app.tools.base_tool import BaseTool

logger = logging.getLogger("cyberscore.tools.reputation")


class ReputationTool(BaseTool):
    """IP reputation checker using AbuseIPDB and VirusTotal."""

    ABUSEIPDB_BASE = "https://api.abuseipdb.com/api/v2"
    VIRUSTOTAL_BASE = "https://www.virustotal.com/api/v3"

    def __init__(self) -> None:
        super().__init__(
            name="reputation",
            base_url=self.ABUSEIPDB_BASE,
            timeout=15.0,
        )
        self._abuseipdb_key = settings.abuseipdb_api_key
        self._virustotal_key = settings.virustotal_api_key

    async def check_abuseipdb(self, ip: str) -> dict[str, Any]:
        """Check IP reputation on AbuseIPDB.

        Args:
            ip: IP address to check.

        Returns:
            Dict with abuse confidence score, report count, country.
        """
        url = f"{self.ABUSEIPDB_BASE}/check"
        headers = {
            "Key": self._abuseipdb_key,
            "Accept": "application/json",
        }
        start = time.monotonic()
        try:
            async with get_scan_http_client(
                timeout=self.timeout, headers=headers,
            ) as client:
                response = await client.get(
                    url,
                    params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": ""},
                )
                response.raise_for_status()
                result = response.json()
            duration = time.monotonic() - start
            self._log_call(url, response.status_code, duration)
            data = result.get("data", {})
            return {
                "ip": ip,
                "source": "abuseipdb",
                "abuse_confidence_score": data.get("abuseConfidenceScore", 0),
                "total_reports": data.get("totalReports", 0),
                "country_code": data.get("countryCode"),
                "isp": data.get("isp"),
                "is_public": data.get("isPublic", True),
            }
        except Exception as exc:
            duration = time.monotonic() - start
            self._log_call(url, 0, duration, error=True)
            logger.warning("AbuseIPDB check failed for %s: %s", ip, exc)
            return {"ip": ip, "source": "abuseipdb", "error": True}

    async def check_virustotal(self, ip: str) -> dict[str, Any]:
        """Check IP on VirusTotal (free API tier).

        Args:
            ip: IP address to check.

        Returns:
            Dict with detection stats from VT engines.
        """
        url = f"{self.VIRUSTOTAL_BASE}/ip_addresses/{ip}"
        headers = {
            "x-apikey": self._virustotal_key,
            "Accept": "application/json",
        }
        start = time.monotonic()
        try:
            async with get_scan_http_client(
                timeout=self.timeout, headers=headers,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                result = response.json()
            duration = time.monotonic() - start
            self._log_call(url, response.status_code, duration)
            stats = result.get("data", {}).get("attributes", {}).get(
                "last_analysis_stats", {}
            )
            return {
                "ip": ip,
                "source": "virustotal",
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "harmless": stats.get("harmless", 0),
                "undetected": stats.get("undetected", 0),
            }
        except Exception as exc:
            duration = time.monotonic() - start
            self._log_call(url, 0, duration, error=True)
            logger.warning("VirusTotal check failed for %s: %s", ip, exc)
            return {"ip": ip, "source": "virustotal", "error": True}

    async def check_ip(self, ip: str) -> dict[str, Any]:
        """Check IP reputation across both AbuseIPDB and VirusTotal.

        Args:
            ip: IP address to check.

        Returns:
            Combined reputation data from both sources.
        """
        abuseipdb_data = await self.check_abuseipdb(ip)
        vt_data = await self.check_virustotal(ip)
        return {
            "ip": ip,
            "source": "abuseipdb+virustotal",
            "abuseipdb": abuseipdb_data,
            "virustotal": vt_data,
            "abuse_confidence_score": abuseipdb_data.get("abuse_confidence_score", 0),
            "vt_malicious": vt_data.get("malicious", 0),
        }
