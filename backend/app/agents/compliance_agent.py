"""Compliance Agent — automated regulatory mapping and assessment.

Maps findings to DORA, NIS2, and RGPD requirements.
Calculates compliance coverage percentages.
Updates the DORA register for ACPR reporting.
"""

import logging
import time
from typing import Any

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.celery_app import celery_app

logger = logging.getLogger("cyberscore.agents.compliance")

DORA_REQUIREMENTS = {
    "art5_governance": "Gouvernance et organisation (Art. 5-6)",
    "art7_risk_framework": "Cadre de gestion des risques TIC (Art. 7-14)",
    "art17_incident_mgmt": "Gestion des incidents TIC (Art. 17-23)",
    "art24_resilience": "Tests de résilience (Art. 24-27)",
    "art28_third_party": "Risques liés aux tiers TIC (Art. 28-30)",
    "art31_concentration": "Risque de concentration (Art. 31-44)",
}


class ComplianceAgent(BaseAgent):
    """Regulatory compliance assessment and mapping."""

    def __init__(self) -> None:
        super().__init__(name="compliance")

    async def execute(self, vendor_id: str, **kwargs: Any) -> AgentResult:
        """Assess compliance for a vendor against specified frameworks.

        Args:
            vendor_id: Vendor UUID.
            **kwargs: framework (str, default "dora"), findings (list).

        Returns:
            AgentResult with compliance assessment.
        """
        framework = kwargs.get("framework", "dora")
        findings = kwargs.get("findings", [])
        start = time.monotonic()

        self.logger.info(
            "Assessing %s compliance for vendor %s", framework, vendor_id
        )

        if framework == "dora":
            assessment = self._assess_dora(findings)
        elif framework == "nis2":
            assessment = self._assess_nis2(findings)
        elif framework == "rgpd":
            assessment = self._assess_rgpd(findings)
        else:
            assessment = {"error": f"Unknown framework: {framework}"}

        duration = time.monotonic() - start
        return AgentResult(
            agent_name=self.name,
            vendor_id=vendor_id,
            success=True,
            data={
                "framework": framework,
                "assessment": assessment,
            },
            duration_seconds=round(duration, 2),
        )

    def _assess_dora(
        self, findings: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Map findings to DORA requirements and calculate coverage.

        Analyzes findings by domain to determine which DORA articles
        are covered by the vendor's security posture.

        Args:
            findings: List of scoring findings with domain_code, severity.

        Returns:
            DORA compliance assessment with coverage per article.
        """
        # Map scoring domains to DORA requirements
        domain_to_dora = {
            "D1": "art7_risk_framework",     # Network security -> ICT risk
            "D2": "art7_risk_framework",     # DNS security -> ICT risk
            "D3": "art7_risk_framework",     # Web security -> ICT risk
            "D4": "art17_incident_mgmt",     # Email security -> incident mgmt
            "D5": "art24_resilience",        # Patching cadence -> resilience
            "D6": "art7_risk_framework",     # IP reputation -> ICT risk
            "D7": "art17_incident_mgmt",     # Leaks -> incident management
            "D8": "art5_governance",         # Regulatory -> governance
        }

        # Track critical findings per DORA requirement
        req_findings: dict[str, list[str]] = {k: [] for k in DORA_REQUIREMENTS}
        for finding in findings:
            domain_code = finding.get("domain_code", finding.get("domain", ""))
            severity = finding.get("severity", "info")
            dora_req = domain_to_dora.get(domain_code)
            if dora_req:
                req_findings[dora_req].append(severity)

        # Calculate coverage based on findings
        coverage: dict[str, str] = {}
        for req_id in DORA_REQUIREMENTS:
            severities = req_findings[req_id]
            if not severities:
                # No findings means no data — not assessed
                coverage[req_id] = "not_assessed"
            elif any(s in ("critical", "high") for s in severities):
                coverage[req_id] = "non_compliant"
            elif any(s == "medium" for s in severities):
                coverage[req_id] = "partial"
            else:
                coverage[req_id] = "full"

        # Third-party risk (art28) always requires assessment data
        if not any(
            f.get("domain_code", f.get("domain", "")) in ("D1", "D6")
            for f in findings
        ):
            coverage["art28_third_party"] = "not_assessed"
        else:
            critical_network = any(
                f.get("severity") in ("critical", "high")
                for f in findings
                if f.get("domain_code", f.get("domain", "")) in ("D1", "D6")
            )
            coverage["art28_third_party"] = "non_compliant" if critical_network else "partial"

        # Concentration risk always needs dedicated analysis
        coverage["art31_concentration"] = "not_assessed"

        covered = sum(1 for v in coverage.values() if v == "full")
        total = len(DORA_REQUIREMENTS)
        return {
            "requirements": DORA_REQUIREMENTS,
            "coverage": coverage,
            "coverage_percent": round(covered / total * 100, 1) if total else 0,
            "total_requirements": total,
            "fully_covered": covered,
            "non_compliant": sum(1 for v in coverage.values() if v == "non_compliant"),
            "not_assessed": sum(1 for v in coverage.values() if v == "not_assessed"),
        }

    def _assess_nis2(
        self, findings: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Assess NIS2 compliance (Art. 21 supply chain security).

        Analyzes network and email security findings for supply chain risks.
        """
        supply_chain_findings = [
            f for f in findings
            if f.get("domain_code", f.get("domain", "")) in ("D1", "D3", "D5", "D6")
        ]
        critical_count = sum(
            1 for f in supply_chain_findings
            if f.get("severity") in ("critical", "high")
        )

        if not supply_chain_findings:
            art21_status = "not_assessed"
        elif critical_count == 0:
            art21_status = "compliant"
        elif critical_count <= 2:
            art21_status = "partial"
        else:
            art21_status = "non_compliant"

        total_checks = 2
        compliant_checks = sum(1 for s in [art21_status] if s == "compliant")
        return {
            "art21_supply_chain": art21_status,
            "art23_notification": "not_assessed",
            "coverage_percent": round(compliant_checks / total_checks * 100, 1),
            "critical_findings": critical_count,
        }

    def _assess_rgpd(
        self, findings: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Assess RGPD compliance indicators from D7 (leaks) and D8 (regulatory) findings."""
        d8_findings = [
            f for f in findings
            if f.get("domain_code", f.get("domain", "")) == "D8"
        ]
        d7_findings = [
            f for f in findings
            if f.get("domain_code", f.get("domain", "")) == "D7"
        ]

        # Check if privacy policy finding exists (absence = finding)
        privacy_missing = any(
            "confidentialité" in f.get("title", "").lower() or "privacy" in f.get("title", "").lower()
            for f in d8_findings
        )
        legal_missing = any(
            "mentions légales" in f.get("title", "").lower() or "legal" in f.get("title", "").lower()
            for f in d8_findings
        )
        has_breaches = any(
            "breach" in f.get("title", "").lower() or "fuite" in f.get("title", "").lower()
            for f in d7_findings
        )

        checks = {
            "privacy_policy_present": not privacy_missing,
            "legal_notices_present": not legal_missing,
            "no_known_breaches": not has_breaches,
        }
        compliant = sum(1 for v in checks.values() if v)
        total = len(checks)

        return {
            **checks,
            "coverage_percent": round(compliant / total * 100, 1) if total else 0,
        }


@celery_app.task(name="app.agents.compliance_agent.assess_compliance")
def assess_compliance(
    vendor_id: str,
    framework: str = "dora",
) -> dict[str, Any]:
    """Celery task: assess compliance for a vendor."""
    import asyncio

    agent = ComplianceAgent()
    result = asyncio.run(
        agent.execute(vendor_id, framework=framework)
    )
    return result.data
