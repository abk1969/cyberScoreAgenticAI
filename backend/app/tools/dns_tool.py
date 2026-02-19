"""DNS Tool — resolve DNS records for domain security analysis.

Uses dnspython for direct DNS resolution. Checks A, AAAA, MX,
NS, TXT, SPF, DKIM, DMARC, DNSSEC, and CAA records.
No external API needed — queries DNS directly.
"""

import logging
from typing import Any

import dns.resolver
import dns.rdatatype

from app.tools.base_tool import BaseTool

logger = logging.getLogger("mh_cyberscore.tools.dns")


class DNSTool(BaseTool):
    """DNS resolution tool using dnspython."""

    def __init__(self) -> None:
        super().__init__(name="dns", base_url="", timeout=10.0)
        self._resolver = dns.resolver.Resolver()
        self._resolver.timeout = 10
        self._resolver.lifetime = 10

    async def resolve(self, domain: str) -> dict[str, Any]:
        """Resolve all relevant DNS records for a domain.

        Args:
            domain: Target domain.

        Returns:
            Dict with all DNS records organized by type.
        """
        results: dict[str, Any] = {"domain": domain, "source": "dns"}

        for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CAA"]:
            try:
                answers = self._resolver.resolve(domain, rtype)
                results[rtype] = [str(r) for r in answers]
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                results[rtype] = []
            except Exception:
                results[rtype] = []

        # SPF (from TXT records)
        results["spf"] = self._extract_spf(results.get("TXT", []))

        # DMARC
        results["dmarc"] = await self._check_dmarc(domain)

        # DKIM (common selectors)
        results["dkim"] = await self._check_dkim(domain)

        # DNSSEC
        results["dnssec"] = await self._check_dnssec(domain)

        # MTA-STS
        results["mta_sts"] = await self._check_mta_sts(domain)

        # BIMI
        results["bimi"] = await self._check_bimi(domain)

        return results

    def _extract_spf(self, txt_records: list[str]) -> dict[str, Any]:
        """Extract SPF record from TXT records."""
        for record in txt_records:
            if "v=spf1" in record:
                return {"present": True, "record": record}
        return {"present": False, "record": None}

    async def _check_dmarc(self, domain: str) -> dict[str, Any]:
        """Check DMARC record at _dmarc.domain."""
        try:
            answers = self._resolver.resolve(f"_dmarc.{domain}", "TXT")
            for record in answers:
                txt = str(record)
                if "v=DMARC1" in txt:
                    policy = "none"
                    if "p=reject" in txt:
                        policy = "reject"
                    elif "p=quarantine" in txt:
                        policy = "quarantine"
                    return {"present": True, "record": txt, "policy": policy}
        except Exception:
            pass
        return {"present": False, "record": None, "policy": None}

    async def _check_dkim(
        self, domain: str, selectors: list[str] | None = None
    ) -> dict[str, Any]:
        """Check DKIM for common selectors."""
        selectors = selectors or [
            "default", "google", "selector1", "selector2", "k1", "dkim",
        ]
        found: list[str] = []
        for selector in selectors:
            try:
                self._resolver.resolve(
                    f"{selector}._domainkey.{domain}", "TXT"
                )
                found.append(selector)
            except Exception:
                continue
        return {"present": len(found) > 0, "selectors_found": found}

    async def _check_dnssec(self, domain: str) -> dict[str, Any]:
        """Check if DNSSEC is enabled for domain."""
        try:
            answers = self._resolver.resolve(domain, "DNSKEY")
            return {"enabled": True, "keys": len(list(answers))}
        except Exception:
            return {"enabled": False, "keys": 0}

    async def _check_mta_sts(self, domain: str) -> dict[str, Any]:
        """Check MTA-STS record at _mta-sts.domain."""
        try:
            answers = self._resolver.resolve(f"_mta-sts.{domain}", "TXT")
            for record in answers:
                txt = str(record)
                if "v=STSv1" in txt:
                    return {"present": True, "record": txt}
        except Exception:
            pass
        return {"present": False, "record": None}

    async def _check_bimi(self, domain: str) -> dict[str, Any]:
        """Check BIMI record at default._bimi.domain."""
        try:
            answers = self._resolver.resolve(f"default._bimi.{domain}", "TXT")
            for record in answers:
                txt = str(record)
                if "v=BIMI1" in txt:
                    return {"present": True, "record": txt}
        except Exception:
            pass
        return {"present": False, "record": None}
