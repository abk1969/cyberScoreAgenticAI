"""D5 — Patching Cadence analyzer (weight: 15%).

Analyzes CVE exposure, known vulnerabilities matching detected
software versions, and time since patch availability.
"""

from typing import Any

from app.services.domain_analyzers.base import (
    BaseDomainAnalyzer,
    DomainResult,
    FindingData,
)

CRITICALITY_FACTORS = {
    "critical": 2.0,  # CVSS >= 9.0
    "high": 1.5,      # CVSS 7.0-8.9
    "medium": 1.0,    # CVSS 4.0-6.9
    "low": 0.5,       # CVSS < 4.0
}


class PatchingCadenceAnalyzer(BaseDomainAnalyzer):
    """D5: Analyzes patching cadence and CVE exposure."""

    domain_code = "D5"
    domain_name = "Cadence de Patching"

    async def analyze(
        self, domain: str, raw_data: dict[str, Any]
    ) -> DomainResult:
        """Analyze patching cadence from CVE data."""
        findings: list[FindingData] = []
        cves = raw_data.get("cves", [])

        for cve in cves:
            cvss = cve.get("cvss_score", 0.0)
            severity = self._cvss_to_severity(cvss)
            findings.append(FindingData(
                domain="D5",
                title=f"CVE détectée: {cve.get('id', 'Unknown')}",
                description=cve.get("description", "Vulnérabilité connue."),
                severity=severity,
                cvss_score=cvss,
                source="nvd",
                evidence=f"CVE: {cve.get('id')} — CVSS: {cvss}",
                recommendation=f"Appliquer le correctif pour {cve.get('id')}.",
            ))

        score = self.calculate_score(findings)
        return DomainResult(
            domain_code=self.domain_code,
            domain_name=self.domain_name,
            score=score,
            grade=self.score_to_grade(score),
            findings=findings,
            confidence=0.7,
        )

    @staticmethod
    def _cvss_to_severity(cvss: float) -> str:
        if cvss >= 9.0:
            return "critical"
        if cvss >= 7.0:
            return "high"
        if cvss >= 4.0:
            return "medium"
        return "low"
