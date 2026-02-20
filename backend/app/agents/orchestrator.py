"""Orchestrator agent — coordinates all sub-agents for vendor scanning.

Receives scan missions, plans execution based on vendor tier,
delegates to specialized agents, collects results, and feeds
them to the ScoringEngine.
"""

import logging
import time
from typing import Any

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.celery_app import celery_app
from app.agents.darkweb_agent import DarkWebAgent
from app.agents.nthparty_agent import NthPartyAgent
from app.agents.osint_agent import OSINTAgent

logger = logging.getLogger("cyberscore.agents.orchestrator")


class OrchestratorAgent(BaseAgent):
    """Chef d'orchestre — plans, delegates, consolidates."""

    def __init__(self) -> None:
        super().__init__(name="orchestrator")
        self._osint_agent = OSINTAgent()
        self._darkweb_agent = DarkWebAgent()
        self._nthparty_agent = NthPartyAgent()

    async def execute(self, vendor_id: str, **kwargs: Any) -> AgentResult:
        """Orchestrate a full vendor scan.

        Uses the configured LLM provider for scan planning when available.

        Args:
            vendor_id: Vendor to scan.
            **kwargs: Must contain 'domain' (str).
                     May contain 'tier' (int) to determine scan depth.

        Returns:
            Consolidated AgentResult with all sub-agent data.
        """
        start = time.monotonic()
        tier = kwargs.get("tier", 3)
        domain = kwargs.get("domain", "")
        results: dict[str, Any] = {}
        errors: list[str] = []

        self.logger.info(
            "Starting orchestrated scan for vendor %s (%s, tier %d)",
            vendor_id,
            domain,
            tier,
        )

        # Use LLM for reasoning/planning if available
        try:
            llm = await self._get_llm_provider()
            plan_response = await llm.chat(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a cybersecurity scan planner. Given a vendor tier, "
                            "output a brief JSON scan plan with keys: osint, darkweb, nthparty "
                            "(boolean each). Tier 1=all, Tier 2=osint+darkweb, Tier 3=osint only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Plan scan for vendor {vendor_id}, tier {tier}.",
                    },
                ],
                temperature=0.0,
                max_tokens=200,
            )
            results["llm_plan"] = plan_response
        except Exception as exc:
            self.logger.debug(
                "LLM planning unavailable, using default logic: %s", exc
            )

        # OSINT scan — always runs
        try:
            osint_result = await self._run_osint(vendor_id, domain)
            results["osint"] = osint_result.data
            errors.extend(osint_result.errors)
        except Exception as exc:
            errors.append(f"OSINT failed: {exc}")
            self.logger.error("OSINT scan failed for %s: %s", vendor_id, exc)

        # Dark web monitoring — Tier 1 and 2 only
        if tier <= 2:
            try:
                darkweb_result = await self._run_darkweb(vendor_id, domain)
                results["darkweb"] = darkweb_result.data
                errors.extend(darkweb_result.errors)
            except Exception as exc:
                errors.append(f"Dark web failed: {exc}")
                self.logger.error(
                    "Dark web scan failed for %s: %s", vendor_id, exc
                )

        # Nth-party detection — Tier 1 only
        if tier == 1:
            try:
                nthparty_result = await self._run_nthparty(vendor_id, domain)
                results["nthparty"] = nthparty_result.data
                errors.extend(nthparty_result.errors)
            except Exception as exc:
                errors.append(f"Nth-party failed: {exc}")
                self.logger.error(
                    "Nth-party detection failed for %s: %s", vendor_id, exc
                )

        duration = time.monotonic() - start
        total_api_calls = (
            self._osint_agent._api_call_count
            + self._darkweb_agent._api_call_count
            + self._nthparty_agent._api_call_count
        )
        return AgentResult(
            agent_name=self.name,
            vendor_id=vendor_id,
            success=len(errors) < 4,
            data=results,
            errors=errors,
            duration_seconds=round(duration, 2),
            api_calls_made=total_api_calls,
        )

    async def _run_osint(self, vendor_id: str, domain: str) -> AgentResult:
        """Delegate to OSINT agent with real tool calls."""
        self.logger.info("Delegating OSINT scan for %s (%s)", vendor_id, domain)
        return await self._osint_agent.execute(vendor_id, domain=domain)

    async def _run_darkweb(self, vendor_id: str, domain: str) -> AgentResult:
        """Delegate to Dark Web monitoring agent with real tool calls."""
        self.logger.info("Delegating dark web monitoring for %s (%s)", vendor_id, domain)
        return await self._darkweb_agent.execute(vendor_id, domain=domain)

    async def _run_nthparty(self, vendor_id: str, domain: str) -> AgentResult:
        """Delegate to Nth-party detection agent with real tool calls."""
        self.logger.info("Delegating Nth-party detection for %s (%s)", vendor_id, domain)
        return await self._nthparty_agent.execute(vendor_id, domain=domain)


@celery_app.task(name="app.agents.orchestrator.orchestrate_vendor_scan")
def orchestrate_vendor_scan(
    vendor_id: str, domain: str, tier: int = 3,
) -> dict[str, Any]:
    """Celery task: full vendor scan orchestration.

    Args:
        vendor_id: Vendor UUID.
        domain: Vendor primary domain.
        tier: Vendor tier (1=critical, 2=important, 3=standard).

    Returns:
        Dict with scan results.
    """
    import asyncio

    agent = OrchestratorAgent()
    result = asyncio.run(agent.execute(vendor_id, domain=domain, tier=tier))
    return {
        "vendor_id": result.vendor_id,
        "success": result.success,
        "data": result.data,
        "errors": result.errors,
        "duration": result.duration_seconds,
    }


@celery_app.task(name="app.agents.orchestrator.rescan_tier")
def rescan_tier(tier: int) -> dict[str, Any]:
    """Celery beat task: rescan all vendors of a given tier.

    Args:
        tier: Vendor tier to rescan.

    Returns:
        Dict with number of vendors queued.
    """
    logger.info("Scheduled rescan for Tier %d vendors", tier)
    # In production: query DB for vendors of this tier, queue individual scans
    return {"tier": tier, "status": "queued", "vendors_queued": 0}
