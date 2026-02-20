"""Compliance service — DORA, NIS2, RGPD mapping and coverage calculation."""

import logging
from typing import Any

logger = logging.getLogger("cyberscore.services.compliance")

DORA_ARTICLES = {
    "art28_risk_mgmt": "Gestion des risques tiers TIC (Art. 28)",
    "art29_contracts": "Dispositions contractuelles (Art. 29)",
    "art30_monitoring": "Surveillance et audit (Art. 30)",
}


class ComplianceService:
    """Service for regulatory compliance assessment."""

    def map_finding_to_dora(
        self, finding: dict[str, Any]
    ) -> list[str]:
        """Map a finding to applicable DORA articles."""
        articles: list[str] = []
        domain = finding.get("domain", "")
        if domain in ("D1", "D2", "D3", "D5"):
            articles.append("art28_risk_mgmt")
        if domain in ("D7", "D8"):
            articles.append("art30_monitoring")
        return articles

    def get_dora_coverage(
        self, findings: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate DORA coverage percentage."""
        covered_articles: set[str] = set()
        for finding in findings:
            covered_articles.update(self.map_finding_to_dora(finding))

        total = len(DORA_ARTICLES)
        covered = len(covered_articles & set(DORA_ARTICLES.keys()))
        return {
            "coverage_percent": round(covered / total * 100, 1) if total else 0,
            "covered_articles": list(covered_articles),
            "total_articles": total,
        }
