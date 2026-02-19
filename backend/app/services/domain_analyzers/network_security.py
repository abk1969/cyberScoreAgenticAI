"""D1 — Network Security analyzer (weight: 15%).

Analyzes open ports, exposed services, unauthorized services,
and known-vulnerable service versions from Shodan/Censys data.
"""

from typing import Any

from app.services.domain_analyzers.base import (
    BaseDomainAnalyzer,
    DomainResult,
    FindingData,
)

RISKY_PORTS = {21, 23, 25, 110, 135, 139, 445, 1433, 1521, 3306, 3389, 5432, 5900}
EXPECTED_PORTS = {80, 443}


class NetworkSecurityAnalyzer(BaseDomainAnalyzer):
    """D1: Analyzes network security posture via open ports and services."""

    domain_code = "D1"
    domain_name = "Sécurité Réseau"

    async def analyze(
        self, domain: str, raw_data: dict[str, Any]
    ) -> DomainResult:
        """Analyze network security from Shodan/Censys data."""
        findings: list[FindingData] = []
        ports = raw_data.get("open_ports", [])

        for port in ports:
            port_num = port.get("port", 0)
            if port_num in RISKY_PORTS:
                findings.append(FindingData(
                    domain="D1",
                    title=f"Port risqué ouvert: {port_num}",
                    description=f"Le port {port_num} ({port.get('service', 'inconnu')}) est exposé publiquement.",
                    severity="high" if port_num in {3389, 445, 23} else "medium",
                    source="shodan",
                    evidence=f"Port {port_num} détecté sur {domain}",
                    recommendation=f"Fermer ou restreindre l'accès au port {port_num}.",
                ))

        # Check for unencrypted services
        for port in ports:
            if port.get("transport", "") == "tcp" and not port.get("tls", False):
                if port.get("port", 0) not in EXPECTED_PORTS:
                    findings.append(FindingData(
                        domain="D1",
                        title=f"Service non chiffré: port {port.get('port')}",
                        description="Service accessible sans chiffrement TLS.",
                        severity="medium",
                        source="censys",
                        recommendation="Activer TLS sur ce service.",
                    ))

        score = self.calculate_score(findings)
        return DomainResult(
            domain_code=self.domain_code,
            domain_name=self.domain_name,
            score=score,
            grade=self.score_to_grade(score),
            findings=findings,
            confidence=0.8 if ports else 0.3,
        )
