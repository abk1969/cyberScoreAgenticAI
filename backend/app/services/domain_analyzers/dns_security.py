"""D2 — DNS Security analyzer (weight: 10%).

Evaluates SPF, DKIM, DMARC, DNSSEC, and CAA records.
"""

from typing import Any

from app.services.domain_analyzers.base import (
    BaseDomainAnalyzer,
    DomainResult,
    FindingData,
)


class DNSSecurityAnalyzer(BaseDomainAnalyzer):
    """D2: Analyzes DNS security configuration."""

    domain_code = "D2"
    domain_name = "Sécurité DNS"

    async def analyze(
        self, domain: str, raw_data: dict[str, Any]
    ) -> DomainResult:
        """Analyze DNS security posture."""
        findings: list[FindingData] = []
        dns_data = raw_data.get("dns", {})

        # SPF check
        spf = dns_data.get("spf", {})
        if not spf.get("present"):
            findings.append(FindingData(
                domain="D2", title="SPF absent",
                description="Aucun enregistrement SPF détecté.",
                severity="high", cvss_score=5.0, source="dns",
                recommendation="Configurer un enregistrement SPF.",
            ))

        # DKIM check
        dkim = dns_data.get("dkim", {})
        if not dkim.get("present"):
            findings.append(FindingData(
                domain="D2", title="DKIM absent",
                description="Aucun enregistrement DKIM détecté.",
                severity="high", cvss_score=5.0, source="dns",
                recommendation="Configurer DKIM pour le domaine.",
            ))

        # DMARC check
        dmarc = dns_data.get("dmarc", {})
        if not dmarc.get("present"):
            findings.append(FindingData(
                domain="D2", title="DMARC absent",
                description="Aucune politique DMARC détectée.",
                severity="critical", cvss_score=7.0, source="dns",
                recommendation="Configurer DMARC avec p=quarantine ou p=reject.",
            ))
        elif dmarc.get("policy") == "none":
            findings.append(FindingData(
                domain="D2", title="DMARC policy=none",
                description="DMARC est configuré mais la politique est 'none' (pas de protection).",
                severity="medium", cvss_score=4.0, source="dns",
                recommendation="Passer la politique DMARC à quarantine ou reject.",
            ))

        # DNSSEC check
        dnssec = dns_data.get("dnssec", {})
        if not dnssec.get("enabled"):
            findings.append(FindingData(
                domain="D2", title="DNSSEC non activé",
                description="DNSSEC n'est pas activé pour ce domaine.",
                severity="medium", cvss_score=3.5, source="dns",
                recommendation="Activer DNSSEC.",
            ))

        # CAA check
        caa = dns_data.get("CAA", [])
        if not caa:
            findings.append(FindingData(
                domain="D2", title="Enregistrement CAA absent",
                description="Aucun enregistrement CAA limitant les CA autorisées.",
                severity="low", cvss_score=2.0, source="dns",
                recommendation="Ajouter un enregistrement CAA.",
            ))

        score = self.calculate_score(findings)
        return DomainResult(
            domain_code=self.domain_code,
            domain_name=self.domain_name,
            score=score,
            grade=self.score_to_grade(score),
            findings=findings,
            confidence=0.95,
        )
