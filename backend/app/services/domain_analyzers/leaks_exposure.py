"""D7 — Leaks & Exposure analyzer (weight: 15%).

Analyzes data breaches, credential leaks, paste sites, and exposed secrets.
"""

from typing import Any

from app.services.domain_analyzers.base import (
    BaseDomainAnalyzer,
    DomainResult,
    FindingData,
)


class LeaksExposureAnalyzer(BaseDomainAnalyzer):
    """D7: Analyzes data breaches and credential exposure."""

    domain_code = "D7"
    domain_name = "Fuites & Exposition"

    async def analyze(
        self, domain: str, raw_data: dict[str, Any]
    ) -> DomainResult:
        """Analyze leaks and exposure."""
        findings: list[FindingData] = []
        hibp = raw_data.get("hibp", {})

        breaches = hibp.get("breaches", [])
        for breach in breaches:
            name = breach.get("Name", "Unknown")
            date = breach.get("BreachDate", "Unknown")
            count = breach.get("PwnCount", 0)
            severity = "critical" if count > 100000 else "high" if count > 10000 else "medium"

            findings.append(FindingData(
                domain="D7",
                title=f"Breach détectée: {name}",
                description=f"Fuite de données '{name}' le {date} — {count:,} comptes affectés.",
                severity=severity,
                source="hibp",
                evidence=f"HIBP: {name} ({date})",
                recommendation="Vérifier l'impact, notifier les utilisateurs, reset des credentials.",
            ))

        # GitHub secrets
        github_secrets = raw_data.get("github_secrets", [])
        for secret in github_secrets:
            findings.append(FindingData(
                domain="D7",
                title=f"Secret exposé sur GitHub: {secret.get('type', 'API key')}",
                description=f"Un secret de type {secret.get('type')} a été trouvé dans un repo public.",
                severity="critical",
                source="github_scan",
                recommendation="Révoquer immédiatement le secret et le supprimer du repo.",
            ))

        score = self.calculate_score(findings)
        return DomainResult(
            domain_code=self.domain_code,
            domain_name=self.domain_name,
            score=score,
            grade=self.score_to_grade(score),
            findings=findings,
            confidence=0.9,
        )
