"""CyberScore Scoring Engine — main scoring orchestration.

Calculates global score (0-1000) and grade (A-F) by aggregating
8 domain scores with configurable weights and criticality factors.

Formula: score_global = Σ(score_domain_i × weight_i × 10)
Grade: A(800-1000), B(600-799), C(400-599), D(200-399), F(0-199)
"""

import logging
from typing import Any

from app.services.domain_analyzers.base import DomainResult
from app.services.domain_analyzers import (
    DNSSecurityAnalyzer,
    EmailSecurityAnalyzer,
    IPReputationAnalyzer,
    LeaksExposureAnalyzer,
    NetworkSecurityAnalyzer,
    PatchingCadenceAnalyzer,
    RegulatoryPresenceAnalyzer,
    WebSecurityAnalyzer,
)
from app.utils.constants import (
    DEFAULT_DOMAIN_WEIGHTS,
    GRADE_THRESHOLDS,
    SIZE_NORMALIZATION,
)

logger = logging.getLogger("cyberscore.scoring")


class ScoringEngine:
    """Main scoring engine for CyberScore.

    Orchestrates all 8 domain analyzers, applies weights and
    normalization, calculates global score and grade.
    """

    def __init__(
        self,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.weights = weights or DEFAULT_DOMAIN_WEIGHTS
        self.analyzers = {
            "D1": NetworkSecurityAnalyzer(),
            "D2": DNSSecurityAnalyzer(),
            "D3": WebSecurityAnalyzer(),
            "D4": EmailSecurityAnalyzer(),
            "D5": PatchingCadenceAnalyzer(),
            "D6": IPReputationAnalyzer(),
            "D7": LeaksExposureAnalyzer(),
            "D8": RegulatoryPresenceAnalyzer(),
        }

    async def score_vendor(
        self,
        vendor_id: str,
        raw_data: dict[str, Any],
        employee_count: int = 0,
    ) -> dict[str, Any]:
        """Calculate the complete score for a vendor.

        Args:
            vendor_id: Vendor UUID.
            raw_data: Raw OSINT data collected by agents.
            employee_count: Vendor employee count for size normalization.

        Returns:
            Dict with global_score, grade, domain_scores, findings.
        """
        domain_results: list[DomainResult] = []

        for code, analyzer in self.analyzers.items():
            try:
                result = await analyzer.analyze(
                    domain=raw_data.get("domain", ""),
                    raw_data=raw_data,
                )
                domain_results.append(result)
            except Exception as exc:
                logger.error(
                    "Analyzer %s failed for vendor %s: %s",
                    code, vendor_id, exc,
                )
                domain_results.append(DomainResult(
                    domain_code=code,
                    domain_name=analyzer.domain_name,
                    score=50,
                    grade="C",
                    confidence=0.0,
                ))

        # Calculate global score
        global_score = self._calculate_global_score(domain_results)

        # Apply size normalization
        size_factor = self.get_size_factor(employee_count)
        global_score = int(global_score * size_factor)
        global_score = max(0, min(1000, global_score))

        grade = self.get_grade(global_score)

        # Collect all findings
        all_findings = []
        for result in domain_results:
            all_findings.extend(result.findings)

        domain_scores = {
            r.domain_code: {
                "name": r.domain_name,
                "score": r.score,
                "grade": r.grade,
                "finding_count": len(r.findings),
                "confidence": r.confidence,
            }
            for r in domain_results
        }

        return {
            "vendor_id": vendor_id,
            "global_score": global_score,
            "grade": grade,
            "domain_scores": domain_scores,
            "findings": all_findings,
            "total_findings": len(all_findings),
        }

    def _calculate_global_score(
        self, domain_results: list[DomainResult]
    ) -> float:
        """Calculate weighted global score from domain results.

        Args:
            domain_results: Results from all 8 domain analyzers.

        Returns:
            Global score 0-1000.
        """
        score = 0.0
        for result in domain_results:
            weight = self.weights.get(result.domain_code, 0.1)
            score += result.score * weight * 10
        return score

    @staticmethod
    def get_grade(score: int) -> str:
        """Map global score (0-1000) to grade (A-F).

        Args:
            score: Global score.

        Returns:
            Grade letter.
        """
        for grade, (low, high) in GRADE_THRESHOLDS.items():
            if low <= score <= high:
                return grade
        return "F"

    @staticmethod
    def get_size_factor(employee_count: int) -> float:
        """Get size normalization factor.

        Args:
            employee_count: Number of employees.

        Returns:
            Normalization multiplier.
        """
        if employee_count < 10:
            return SIZE_NORMALIZATION["micro"]
        if employee_count < 250:
            return SIZE_NORMALIZATION["pme"]
        if employee_count < 5000:
            return SIZE_NORMALIZATION["eti"]
        return SIZE_NORMALIZATION["grand_groupe"]

    async def score_portfolio(
        self,
        vendors: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Score multiple vendors.

        Args:
            vendors: List of dicts with vendor_id, raw_data, employee_count.

        Returns:
            List of scoring results.
        """
        results = []
        for vendor in vendors:
            result = await self.score_vendor(
                vendor_id=vendor["vendor_id"],
                raw_data=vendor.get("raw_data", {}),
                employee_count=vendor.get("employee_count", 0),
            )
            results.append(result)
        return results
