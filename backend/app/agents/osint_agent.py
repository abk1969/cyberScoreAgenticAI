"""OSINT Agent — collects public data legally for vendor scoring.

Calls all configured MCP tools for a given domain, aggregates
results by scoring domain (D1-D8), with confidence scores
and source attribution for every finding.

LEGAL RULES (STRICT):
1. Only publicly accessible data (no scraping behind login)
2. Respect robots.txt
3. Rate limit: max 1 req/sec per domain
4. No aggressive active scanning
5. Official APIs with registered keys only
6. No personal data collection
7. Legal basis: legitimate interest (RGPD art. 6.1.f)
8. Processing register updated for each OSINT source
9. Retention: raw data 90 days, aggregated scores 3 years
10. Vendor right of opposition documented
"""

import asyncio
import logging
import re
import time
from typing import Any

import httpx

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.celery_app import celery_app
from app.tools.censys_tool import CensysTool
from app.tools.ct_logs_tool import CTLogsTool
from app.tools.cve_tool import CVETool
from app.tools.dns_tool import DNSTool
from app.tools.hibp_tool import HIBPTool
from app.tools.reputation_tool import ReputationTool
from app.tools.shodan_tool import ShodanTool
from app.tools.ssl_tool import SSLTool

logger = logging.getLogger("mh_cyberscore.agents.osint")


class OSINTAgent(BaseAgent):
    """Collecteur OSINT — gathers public intelligence on vendors."""

    def __init__(self) -> None:
        super().__init__(name="osint", timeout=30.0, rate_limit_per_sec=1.0)
        self._shodan = ShodanTool()
        self._censys = CensysTool()
        self._dns = DNSTool()
        self._ssl = SSLTool()
        self._cve = CVETool()
        self._hibp = HIBPTool()
        self._reputation = ReputationTool()
        self._ct_logs = CTLogsTool()

    async def execute(self, vendor_id: str, **kwargs: Any) -> AgentResult:
        """Execute OSINT collection for a vendor domain.

        Args:
            vendor_id: Vendor UUID.
            **kwargs: Must contain 'domain' (str).

        Returns:
            AgentResult with data organized by scoring domain D1-D8.
        """
        domain = kwargs.get("domain", "")
        start = time.monotonic()
        data: dict[str, Any] = {}
        errors: list[str] = []

        self.logger.info("Starting OSINT scan for %s (%s)", vendor_id, domain)

        # D1 — Network Security (Shodan + Censys)
        try:
            data["D1_network"] = await self._rate_limited_call(
                self._scan_network(domain), "shodan+censys", domain=domain,
            )
        except Exception as exc:
            errors.append(f"D1 network scan: {exc}")

        # Rate limit between domains
        await asyncio.sleep(1.0)

        # D2 — DNS Security
        try:
            data["D2_dns"] = await self._rate_limited_call(
                self._scan_dns(domain), "dns", domain=domain,
            )
        except Exception as exc:
            errors.append(f"D2 DNS scan: {exc}")

        # D3 — Web Security
        try:
            data["D3_web"] = await self._rate_limited_call(
                self._scan_web(domain), "ssl+headers", domain=domain,
            )
        except Exception as exc:
            errors.append(f"D3 web scan: {exc}")

        # D4 — Email Security (uses DNS data already collected)
        try:
            dns_data = data.get("D2_dns", {})
            data["D4_email"] = self._extract_email_security(domain, dns_data)
        except Exception as exc:
            errors.append(f"D4 email scan: {exc}")

        await asyncio.sleep(1.0)

        # D5 — Patching Cadence (CVE matching from detected services)
        try:
            data["D5_patching"] = await self._rate_limited_call(
                self._scan_patching(domain, data.get("D1_network", {})),
                "nvd", domain=domain,
            )
        except Exception as exc:
            errors.append(f"D5 patching scan: {exc}")

        await asyncio.sleep(1.0)

        # D6 — IP Reputation
        try:
            data["D6_reputation"] = await self._rate_limited_call(
                self._scan_reputation(domain, data.get("D1_network", {})),
                "abuseipdb+virustotal", domain=domain,
            )
        except Exception as exc:
            errors.append(f"D6 reputation scan: {exc}")

        await asyncio.sleep(1.0)

        # D7 — Leaks & Exposure
        try:
            data["D7_leaks"] = await self._rate_limited_call(
                self._scan_leaks(domain), "hibp", domain=domain,
            )
        except Exception as exc:
            errors.append(f"D7 leaks scan: {exc}")

        # D8 — Regulatory Presence
        try:
            data["D8_regulatory"] = await self._rate_limited_call(
                self._scan_regulatory(domain), "web_scrape", domain=domain,
            )
        except Exception as exc:
            errors.append(f"D8 regulatory scan: {exc}")

        duration = time.monotonic() - start
        return AgentResult(
            agent_name=self.name,
            vendor_id=vendor_id,
            success=len(errors) < 4,  # Allow partial success
            data=data,
            errors=errors,
            duration_seconds=round(duration, 2),
            api_calls_made=self._api_call_count,
        )

    async def _scan_network(self, domain: str) -> dict[str, Any]:
        """D1: Scan network via Shodan + Censys APIs."""
        shodan_data = await self._shodan.search(domain)
        await asyncio.sleep(1.0)
        censys_data = await self._censys.search_hosts(domain)

        # Merge open ports from both sources
        open_ports = shodan_data.get("open_ports", [])

        # Extract additional ports from Censys hits
        censys_hits = censys_data.get("data", {}).get("result", {}).get("hits", [])
        for hit in censys_hits if isinstance(censys_hits, list) else []:
            for svc in hit.get("services", []):
                port_num = svc.get("port")
                if port_num and not any(p.get("port") == port_num for p in open_ports):
                    open_ports.append({
                        "port": port_num,
                        "transport": svc.get("transport_protocol", "tcp"),
                        "service": svc.get("service_name", "unknown"),
                        "tls": svc.get("tls", {}).get("version_selected", "") != "",
                    })

        return {
            "domain": domain,
            "source": "shodan+censys",
            "open_ports": open_ports,
            "ips": shodan_data.get("ips", []),
            "shodan_raw": shodan_data,
            "censys_raw": censys_data,
            "confidence": 0.8 if open_ports else 0.3,
        }

    async def _scan_dns(self, domain: str) -> dict[str, Any]:
        """D2: Check DNS configuration via real dnspython resolution."""
        dns_data = await self._dns.resolve(domain)
        dns_data["confidence"] = 0.95
        return dns_data

    async def _scan_web(self, domain: str) -> dict[str, Any]:
        """D3: Check web security headers and TLS via real connections."""
        ssl_data = await self._ssl.check(domain)
        await asyncio.sleep(1.0)
        http_headers = await self._ssl.check_http_headers(domain)
        return {
            "domain": domain,
            "source": "ssl+headers",
            "ssl": ssl_data,
            "http_headers": http_headers,
            "confidence": 0.9,
        }

    def _extract_email_security(
        self, domain: str, dns_data: dict[str, Any]
    ) -> dict[str, Any]:
        """D4: Extract email security data from already-collected DNS data."""
        return {
            "domain": domain,
            "source": "dns",
            "dns": {
                "MX": dns_data.get("MX", []),
                "spf": dns_data.get("spf", {}),
                "dkim": dns_data.get("dkim", {}),
                "dmarc": dns_data.get("dmarc", {}),
                "mta_sts": dns_data.get("mta_sts", {}),
                "bimi": dns_data.get("bimi", {}),
            },
            "confidence": 0.9,
        }

    async def _scan_patching(
        self, domain: str, network_data: dict[str, Any]
    ) -> dict[str, Any]:
        """D5: Check CVE exposure based on detected services."""
        cves: list[dict[str, Any]] = []
        open_ports = network_data.get("open_ports", [])

        # Search for CVEs matching detected service versions
        for port_info in open_ports[:5]:  # Limit to 5 services to respect rate limits
            service = port_info.get("service", "")
            version = port_info.get("version", "")
            if service and version:
                keyword = f"{service} {version}"
                try:
                    result = await self._cve.search_by_keyword(keyword)
                    nvd_cves = (
                        result.get("data", {})
                        .get("vulnerabilities", [])
                    )
                    for vuln in nvd_cves[:5]:
                        cve_item = vuln.get("cve", {})
                        metrics = cve_item.get("metrics", {})
                        cvss_data = (
                            metrics.get("cvssMetricV31", [{}])[0]
                            if metrics.get("cvssMetricV31")
                            else metrics.get("cvssMetricV2", [{}])[0]
                            if metrics.get("cvssMetricV2")
                            else {}
                        )
                        cvss_score = cvss_data.get("cvssData", {}).get("baseScore", 0.0)
                        descriptions = cve_item.get("descriptions", [])
                        desc = next(
                            (d.get("value", "") for d in descriptions if d.get("lang") == "en"),
                            descriptions[0].get("value", "") if descriptions else "",
                        )
                        cves.append({
                            "id": cve_item.get("id", ""),
                            "cvss_score": cvss_score,
                            "description": desc[:300],
                            "service": keyword,
                        })
                    await asyncio.sleep(1.0)
                except Exception as exc:
                    logger.warning("CVE search failed for %s: %s", keyword, exc)

        # Also check for CVEs from Shodan vulns if available
        shodan_vulns = network_data.get("shodan_raw", {}).get("vulns", [])
        for vuln_id in shodan_vulns[:5]:
            if vuln_id.startswith("CVE-") and not any(c.get("id") == vuln_id for c in cves):
                try:
                    result = await self._cve.get_cve(vuln_id)
                    nvd_cves = result.get("data", {}).get("vulnerabilities", [])
                    if nvd_cves:
                        cve_item = nvd_cves[0].get("cve", {})
                        metrics = cve_item.get("metrics", {})
                        cvss_data = (
                            metrics.get("cvssMetricV31", [{}])[0]
                            if metrics.get("cvssMetricV31")
                            else {}
                        )
                        cvss_score = cvss_data.get("cvssData", {}).get("baseScore", 0.0)
                        cves.append({
                            "id": vuln_id,
                            "cvss_score": cvss_score,
                            "description": "Detected by Shodan",
                            "service": "shodan_fingerprint",
                        })
                    await asyncio.sleep(1.0)
                except Exception as exc:
                    logger.warning("CVE lookup failed for %s: %s", vuln_id, exc)

        return {
            "domain": domain,
            "source": "nvd",
            "cves": cves,
            "confidence": 0.7 if cves else 0.5,
        }

    async def _scan_reputation(
        self, domain: str, network_data: dict[str, Any]
    ) -> dict[str, Any]:
        """D6: Check IP reputation via AbuseIPDB + VirusTotal."""
        ips = network_data.get("ips", [])
        reputation_results: list[dict[str, Any]] = []

        for ip in ips[:3]:  # Limit to 3 IPs
            combined = await self._reputation.check_ip(ip)
            reputation_results.append(combined)
            await asyncio.sleep(1.0)

        # Aggregate worst scores
        worst_abuse = max(
            (r.get("abuse_confidence_score", 0) for r in reputation_results),
            default=0,
        )
        worst_vt = max(
            (r.get("vt_malicious", 0) for r in reputation_results),
            default=0,
        )

        return {
            "domain": domain,
            "source": "abuseipdb+virustotal",
            "reputation": {
                "abuse_confidence_score": worst_abuse,
                "vt_malicious": worst_vt,
                "ips_checked": len(reputation_results),
                "details": reputation_results,
            },
            "confidence": 0.85 if reputation_results else 0.3,
        }

    async def _scan_leaks(self, domain: str) -> dict[str, Any]:
        """D7: Check for data breaches via HIBP + CT logs."""
        hibp_data = await self._hibp.check_breaches(domain)
        await asyncio.sleep(1.0)
        ct_data = await self._ct_logs.search(domain)

        return {
            "domain": domain,
            "source": "hibp+ct_logs",
            "hibp": hibp_data,
            "ct_logs": ct_data,
            "confidence": 0.9,
        }

    async def _scan_regulatory(self, domain: str) -> dict[str, Any]:
        """D8: Check regulatory presence via passive HTTP checks.

        Checks for common legal/privacy pages with a simple GET.
        """
        privacy_found = False
        legal_found = False
        certifications: list[str] = []

        common_privacy_paths = ["/privacy", "/politique-de-confidentialite", "/privacy-policy"]
        common_legal_paths = ["/mentions-legales", "/legal", "/imprint"]
        cert_patterns = [
            (r"iso\s*27001", "ISO 27001"),
            (r"soc\s*2", "SOC 2"),
            (r"hds", "HDS"),
            (r"secnumcloud", "SecNumCloud"),
            (r"iso\s*27701", "ISO 27701"),
        ]

        try:
            async with httpx.AsyncClient(
                timeout=10.0, follow_redirects=True, max_redirects=3,
            ) as client:
                # Check privacy policy
                for path in common_privacy_paths:
                    try:
                        resp = await client.get(f"https://{domain}{path}")
                        if resp.status_code == 200 and len(resp.text) > 500:
                            privacy_found = True
                            body_lower = resp.text.lower()
                            for pattern, cert_name in cert_patterns:
                                if re.search(pattern, body_lower) and cert_name not in certifications:
                                    certifications.append(cert_name)
                            break
                    except Exception:
                        continue
                    await asyncio.sleep(1.0)

                # Check legal notices
                for path in common_legal_paths:
                    try:
                        resp = await client.get(f"https://{domain}{path}")
                        if resp.status_code == 200 and len(resp.text) > 500:
                            legal_found = True
                            break
                    except Exception:
                        continue
                    await asyncio.sleep(1.0)
        except Exception as exc:
            logger.warning("Regulatory scan failed for %s: %s", domain, exc)

        return {
            "domain": domain,
            "source": "web_scrape",
            "regulatory": {
                "privacy_policy": privacy_found,
                "legal_notices": legal_found,
                "certifications": certifications,
            },
            "confidence": 0.6,
        }


@celery_app.task(name="app.agents.osint_agent.scan_vendor_osint")
def scan_vendor_osint(vendor_id: str, domain: str) -> dict[str, Any]:
    """Celery task: OSINT scan for a vendor.

    Args:
        vendor_id: Vendor UUID.
        domain: Vendor primary domain.

    Returns:
        Dict with OSINT results by scoring domain.
    """
    import asyncio

    agent = OSINTAgent()
    result = asyncio.run(agent.execute(vendor_id, domain=domain))
    return {
        "vendor_id": result.vendor_id,
        "success": result.success,
        "data": result.data,
        "errors": result.errors,
        "duration": result.duration_seconds,
        "audit_log": agent.get_audit_log(),
    }
