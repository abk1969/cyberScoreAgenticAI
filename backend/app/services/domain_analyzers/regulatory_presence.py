"""D8 — Regulatory Presence analyzer (weight: 10%).

Analyzes legal notices, privacy policies, published certifications,
and GDPR compliance indicators.
"""

from typing import Any

from app.services.domain_analyzers.base import (
    BaseDomainAnalyzer,
    DomainResult,
    FindingData,
)

VALUED_CERTIFICATIONS = {
    "iso27001": "ISO 27001",
    "soc2": "SOC 2",
    "hds": "HDS",
    "secnumcloud": "SecNumCloud",
    "iso27701": "ISO 27701",
}


class RegulatoryPresenceAnalyzer(BaseDomainAnalyzer):
    """D8: Analyzes regulatory presence and published certifications."""

    domain_code = "D8"
    domain_name = "Présence Réglementaire"

    async def analyze(
        self, domain: str, raw_data: dict[str, Any]
    ) -> DomainResult:
        """Analyze regulatory presence."""
        findings: list[FindingData] = []
        regulatory = raw_data.get("regulatory", {})

        if not regulatory.get("privacy_policy"):
            findings.append(FindingData(
                domain="D8",
                title="Politique de confidentialité absente",
                description="Aucune politique de confidentialité trouvée sur le site.",
                severity="high",
                source="web_scrape",
                recommendation="Publier une politique de confidentialité conforme RGPD.",
            ))

        if not regulatory.get("legal_notices"):
            findings.append(FindingData(
                domain="D8",
                title="Mentions légales absentes",
                description="Mentions légales non trouvées.",
                severity="medium",
                source="web_scrape",
                recommendation="Ajouter les mentions légales obligatoires.",
            ))

        certifications = regulatory.get("certifications", [])
        if not certifications:
            findings.append(FindingData(
                domain="D8",
                title="Aucune certification publiée",
                description="Aucune certification de sécurité identifiée.",
                severity="low",
                source="web_scrape",
                recommendation="Publier les certifications obtenues (ISO 27001, SOC2, etc.).",
            ))

        score = self.calculate_score(findings)
        # Bonus for certifications
        cert_bonus = min(len(certifications) * 5, 15)
        score = min(100, score + cert_bonus)

        return DomainResult(
            domain_code=self.domain_code,
            domain_name=self.domain_name,
            score=score,
            grade=self.score_to_grade(score),
            findings=findings,
            confidence=0.6,
            metadata={"certifications_found": certifications},
        )
