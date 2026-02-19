"""Dark Web Monitor Agent — surveillance of leaks from LEGAL sources only.

STRICTLY LEGAL sources:
- Have I Been Pwned API (breaches by domain)
- GitHub code search API (exposed secrets via regex — public data only)
- CERT-FR / ANSSI RSS bulletins
- Security news RSS feeds (BleepingComputer, SecurityWeek)

FORBIDDEN:
- Direct dark web access (.onion) without legal authorization
- Purchase of stolen data
- Use of leaked credentials for testing
- Any authentication bypass
"""

import asyncio
import logging
import time
from typing import Any
from xml.etree import ElementTree

import httpx

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.celery_app import celery_app
from app.tools.hibp_tool import HIBPTool

logger = logging.getLogger("mh_cyberscore.agents.darkweb")

CERTFR_RSS_URL = "https://www.cert.ssi.gouv.fr/feed/"
SECURITY_FEEDS = [
    "https://www.bleepingcomputer.com/feed/",
]


class DarkWebAgent(BaseAgent):
    """Dark web monitoring agent — legal sources only."""

    def __init__(self) -> None:
        super().__init__(name="darkweb", timeout=30.0)
        self._hibp = HIBPTool()

    async def execute(self, vendor_id: str, **kwargs: Any) -> AgentResult:
        """Monitor dark web/leak sources for a vendor.

        Args:
            vendor_id: Vendor UUID.
            **kwargs: Must contain 'domain' (str).

        Returns:
            AgentResult with categorized alerts.
        """
        domain = kwargs.get("domain", "")
        start = time.monotonic()
        data: dict[str, Any] = {"alerts": []}
        errors: list[str] = []

        self.logger.info(
            "Starting dark web monitoring for %s (%s)", vendor_id, domain
        )

        # HIBP breach check
        try:
            breaches = await self._rate_limited_call(
                self._check_hibp(domain), "hibp", domain=domain,
            )
            data["hibp_breaches"] = breaches
            # Generate alerts for recent breaches
            for breach in breaches:
                data["alerts"].append({
                    "type": "breach",
                    "severity": "high",
                    "source": "hibp",
                    "title": f"Breach: {breach.get('Name', 'Unknown')}",
                    "date": breach.get("BreachDate"),
                    "count": breach.get("PwnCount", 0),
                })
        except Exception as exc:
            errors.append(f"HIBP check failed: {exc}")

        await asyncio.sleep(1.0)

        # GitHub public code search for exposed secrets
        try:
            secrets = await self._rate_limited_call(
                self._scan_github_secrets(domain), "github_code_search",
                domain=domain,
            )
            data["github_secrets"] = secrets
            for secret in secrets:
                data["alerts"].append({
                    "type": "exposed_secret",
                    "severity": "critical",
                    "source": "github",
                    "title": f"Secret exposed: {secret.get('type', 'unknown')}",
                    "repo": secret.get("repo", ""),
                })
        except Exception as exc:
            errors.append(f"GitHub scan failed: {exc}")

        await asyncio.sleep(1.0)

        # CERT-FR bulletins
        try:
            bulletins = await self._rate_limited_call(
                self._check_certfr(domain), "certfr", domain=domain,
            )
            data["certfr_bulletins"] = bulletins
        except Exception as exc:
            errors.append(f"CERT-FR check failed: {exc}")

        await asyncio.sleep(1.0)

        # Security RSS feeds
        try:
            news = await self._rate_limited_call(
                self._check_security_feeds(domain), "security_rss",
                domain=domain,
            )
            data["security_news"] = news
        except Exception as exc:
            errors.append(f"RSS feeds check failed: {exc}")

        duration = time.monotonic() - start
        return AgentResult(
            agent_name=self.name,
            vendor_id=vendor_id,
            success=len(errors) <= 1,  # Allow 1 error
            data=data,
            errors=errors,
            duration_seconds=round(duration, 2),
            api_calls_made=self._api_call_count,
        )

    async def _check_hibp(self, domain: str) -> list[dict[str, Any]]:
        """Check Have I Been Pwned for breaches related to domain."""
        result = await self._hibp.check_breaches(domain)
        return result.get("breaches", [])

    async def _scan_github_secrets(self, domain: str) -> list[dict[str, Any]]:
        """Search GitHub public code for exposed secrets matching domain.

        Uses the GitHub code search API (unauthenticated, rate-limited).
        Searches for common secret patterns mentioning the domain.
        """
        secrets: list[dict[str, Any]] = []
        search_queries = [
            f'"{domain}" password',
            f'"{domain}" api_key OR apikey OR api-key',
        ]

        async with httpx.AsyncClient(timeout=15.0) as client:
            for query in search_queries:
                try:
                    resp = await client.get(
                        "https://api.github.com/search/code",
                        params={"q": query, "per_page": 5},
                        headers={
                            "Accept": "application/vnd.github.v3+json",
                            "User-Agent": "MH-CyberScore-VRM",
                        },
                    )
                    if resp.status_code == 200:
                        items = resp.json().get("items", [])
                        for item in items[:3]:
                            secrets.append({
                                "type": "potential_secret",
                                "repo": item.get("repository", {}).get("full_name", ""),
                                "path": item.get("path", ""),
                                "url": item.get("html_url", ""),
                            })
                except Exception as exc:
                    logger.warning("GitHub search failed for query '%s': %s", query, exc)
                await asyncio.sleep(2.0)  # GitHub rate limit

        return secrets

    async def _check_certfr(self, domain: str) -> list[dict[str, Any]]:
        """Check CERT-FR/ANSSI RSS feed for mentions of domain."""
        bulletins: list[dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(CERTFR_RSS_URL)
                if resp.status_code == 200:
                    root = ElementTree.fromstring(resp.content)
                    # Extract domain name without TLD for broader matching
                    domain_base = domain.split(".")[0].lower()
                    for item in root.iter("item"):
                        title = item.findtext("title", "").lower()
                        description = item.findtext("description", "").lower()
                        if domain_base in title or domain_base in description:
                            bulletins.append({
                                "title": item.findtext("title", ""),
                                "link": item.findtext("link", ""),
                                "date": item.findtext("pubDate", ""),
                                "source": "cert-fr",
                            })
        except Exception as exc:
            logger.warning("CERT-FR RSS check failed: %s", exc)

        return bulletins

    async def _check_security_feeds(
        self, domain: str
    ) -> list[dict[str, Any]]:
        """Check security RSS feeds for mentions of domain."""
        news: list[dict[str, Any]] = []
        domain_base = domain.split(".")[0].lower()

        async with httpx.AsyncClient(timeout=15.0) as client:
            for feed_url in SECURITY_FEEDS:
                try:
                    resp = await client.get(feed_url)
                    if resp.status_code == 200:
                        root = ElementTree.fromstring(resp.content)
                        for item in root.iter("item"):
                            title = item.findtext("title", "").lower()
                            description = item.findtext("description", "").lower()
                            if domain_base in title or domain_base in description:
                                news.append({
                                    "title": item.findtext("title", ""),
                                    "link": item.findtext("link", ""),
                                    "date": item.findtext("pubDate", ""),
                                    "source": feed_url,
                                })
                except Exception as exc:
                    logger.warning("RSS feed check failed for %s: %s", feed_url, exc)
                await asyncio.sleep(1.0)

        return news


@celery_app.task(name="app.agents.darkweb_agent.monitor_darkweb")
def monitor_darkweb(vendor_id: str, domain: str) -> dict[str, Any]:
    """Celery task: dark web monitoring for a vendor."""
    import asyncio

    agent = DarkWebAgent()
    result = asyncio.run(agent.execute(vendor_id, domain=domain))
    return {
        "vendor_id": result.vendor_id,
        "success": result.success,
        "data": result.data,
        "errors": result.errors,
        "duration": result.duration_seconds,
    }
