"""Base classes for domain analyzers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FindingData:
    """Individual finding from a domain analysis."""

    domain: str
    title: str
    description: str
    severity: str  # critical, high, medium, low, info
    cvss_score: float = 0.0
    source: str = ""
    evidence: str = ""
    recommendation: str = ""


@dataclass
class DomainResult:
    """Result of a single domain analysis."""

    domain_code: str  # D1-D8
    domain_name: str
    score: int  # 0-100
    grade: str  # A-E
    findings: list[FindingData] = field(default_factory=list)
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


SEVERITY_DEDUCTIONS = {
    "critical": 30,
    "high": 20,
    "medium": 10,
    "low": 5,
    "info": 0,
}


class BaseDomainAnalyzer(ABC):
    """Abstract base class for all 8 domain analyzers."""

    domain_code: str = ""
    domain_name: str = ""

    @abstractmethod
    async def analyze(
        self, domain: str, raw_data: dict[str, Any]
    ) -> DomainResult:
        """Analyze a domain and return scored result.

        Args:
            domain: Target domain name.
            raw_data: Raw OSINT data collected for this domain.

        Returns:
            DomainResult with score, grade, and findings.
        """

    def calculate_score(self, findings: list[FindingData]) -> int:
        """Calculate domain score based on findings.

        Starts at 100 and deducts points per finding severity.

        Args:
            findings: List of findings from analysis.

        Returns:
            Score between 0 and 100.
        """
        score = 100
        for finding in findings:
            deduction = SEVERITY_DEDUCTIONS.get(finding.severity, 0)
            score -= deduction
        return max(0, min(100, score))

    @staticmethod
    def score_to_grade(score: int) -> str:
        """Map a 0-100 score to A-E grade.

        Args:
            score: Domain score.

        Returns:
            Grade letter.
        """
        if score >= 80:
            return "A"
        if score >= 60:
            return "B"
        if score >= 40:
            return "C"
        if score >= 20:
            return "D"
        return "E"
