"""D6 — IP Reputation analyzer (weight: 10%).

Analyzes IP reputation from AbuseIPDB, VirusTotal, and blacklists.
"""

from typing import Any

from app.services.domain_analyzers.base import (
    BaseDomainAnalyzer,
    DomainResult,
    FindingData,
)


class IPReputationAnalyzer(BaseDomainAnalyzer):
    """D6: Analyzes IP reputation across multiple sources."""

    domain_code = "D6"
    domain_name = "Réputation IP"

    async def analyze(
        self, domain: str, raw_data: dict[str, Any]
    ) -> DomainResult:
        """Analyze IP reputation."""
        findings: list[FindingData] = []
        reputation = raw_data.get("reputation", {})

        abuse_score = reputation.get("abuse_confidence_score", 0)
        if abuse_score > 50:
            findings.append(FindingData(
                domain="D6",
                title=f"Score d'abus élevé: {abuse_score}%",
                description=f"AbuseIPDB confidence score: {abuse_score}%.",
                severity="critical" if abuse_score > 80 else "high",
                source="abuseipdb",
                recommendation="Investiguer les signalements d'abus.",
            ))

        vt_malicious = reputation.get("vt_malicious", 0)
        if vt_malicious > 0:
            findings.append(FindingData(
                domain="D6",
                title=f"Détections VirusTotal: {vt_malicious}",
                description=f"{vt_malicious} moteurs antivirus signalent cette IP.",
                severity="high" if vt_malicious > 3 else "medium",
                source="virustotal",
                recommendation="Vérifier l'activité réseau de cette IP.",
            ))

        blacklists = reputation.get("blacklists", [])
        if blacklists:
            findings.append(FindingData(
                domain="D6",
                title=f"IP sur {len(blacklists)} blacklist(s)",
                description=f"L'IP est listée sur: {', '.join(blacklists[:5])}.",
                severity="high",
                source="blacklists",
                recommendation="Demander le retrait des blacklists.",
            ))

        score = self.calculate_score(findings)
        return DomainResult(
            domain_code=self.domain_code,
            domain_name=self.domain_name,
            score=score,
            grade=self.score_to_grade(score),
            findings=findings,
            confidence=0.85,
        )
