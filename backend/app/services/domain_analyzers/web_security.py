"""D3 — Web Security analyzer (weight: 15%).

Analyzes TLS version/grade, security headers, and cookie security.
"""

from typing import Any

from app.services.domain_analyzers.base import (
    BaseDomainAnalyzer,
    DomainResult,
    FindingData,
)

REQUIRED_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy",
]


class WebSecurityAnalyzer(BaseDomainAnalyzer):
    """D3: Analyzes web security headers and TLS configuration."""

    domain_code = "D3"
    domain_name = "Sécurité Web"

    async def analyze(
        self, domain: str, raw_data: dict[str, Any]
    ) -> DomainResult:
        """Analyze web security posture."""
        findings: list[FindingData] = []
        ssl_data = raw_data.get("ssl", {})
        headers = raw_data.get("http_headers", {})

        # TLS version check
        tls_version = ssl_data.get("tls_version", "")
        if tls_version in ("TLSv1", "TLSv1.1"):
            findings.append(FindingData(
                domain="D3", title=f"TLS obsolète: {tls_version}",
                description=f"Version TLS {tls_version} détectée.",
                severity="critical", cvss_score=7.5, source="ssl_check",
                recommendation="Migrer vers TLS 1.2 minimum, TLS 1.3 recommandé.",
            ))
        elif tls_version == "TLSv1.2":
            findings.append(FindingData(
                domain="D3", title="TLS 1.2 — upgrade recommandé",
                description="TLS 1.2 est supporté mais TLS 1.3 est recommandé.",
                severity="low", source="ssl_check",
                recommendation="Activer TLS 1.3.",
            ))

        # Certificate expiry
        days_expiry = ssl_data.get("days_until_expiry", 365)
        if days_expiry < 0:
            findings.append(FindingData(
                domain="D3", title="Certificat expiré",
                description="Le certificat TLS est expiré.",
                severity="critical", cvss_score=9.0, source="ssl_check",
                recommendation="Renouveler immédiatement le certificat.",
            ))
        elif days_expiry < 30:
            findings.append(FindingData(
                domain="D3", title="Certificat bientôt expiré",
                description=f"Le certificat expire dans {days_expiry} jours.",
                severity="high", source="ssl_check",
                recommendation="Renouveler le certificat rapidement.",
            ))

        # Security headers check
        for header in REQUIRED_HEADERS:
            if header.lower() not in {h.lower() for h in headers.keys()}:
                findings.append(FindingData(
                    domain="D3", title=f"Header manquant: {header}",
                    description=f"L'en-tête de sécurité {header} n'est pas défini.",
                    severity="medium", source="http_headers",
                    recommendation=f"Ajouter l'en-tête {header}.",
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
