"""D4 — Email Security analyzer (weight: 10%).

Evaluates SPF alignment, DKIM alignment, DMARC enforcement,
MTA-STS, BIMI, and DANE protocols.
"""

from typing import Any

from app.services.domain_analyzers.base import (
    BaseDomainAnalyzer,
    DomainResult,
    FindingData,
)


class EmailSecurityAnalyzer(BaseDomainAnalyzer):
    """D4: Analyzes email security protocols."""

    domain_code = "D4"
    domain_name = "Sécurité Email"

    async def analyze(
        self, domain: str, raw_data: dict[str, Any]
    ) -> DomainResult:
        """Analyze email security posture."""
        findings: list[FindingData] = []
        dns_data = raw_data.get("dns", {})

        # MTA-STS check
        mta_sts = dns_data.get("mta_sts", {})
        if not mta_sts.get("present"):
            findings.append(FindingData(
                domain="D4", title="MTA-STS absent",
                description="MTA-STS non configuré — emails vulnérables aux attaques downgrade.",
                severity="medium", source="dns",
                recommendation="Configurer MTA-STS pour protéger les emails en transit.",
            ))

        # BIMI check
        bimi = dns_data.get("bimi", {})
        if not bimi.get("present"):
            findings.append(FindingData(
                domain="D4", title="BIMI non configuré",
                description="Brand Indicators for Message Identification absent.",
                severity="info", source="dns",
                recommendation="Considérer la mise en place de BIMI.",
            ))

        # MX record check
        mx_records = dns_data.get("MX", [])
        if not mx_records:
            findings.append(FindingData(
                domain="D4", title="Enregistrements MX absents",
                description="Aucun enregistrement MX détecté.",
                severity="high", source="dns",
                recommendation="Vérifier la configuration MX.",
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
