"""Tests for the CyberScore scoring engine."""

import pytest

from app.services.scoring_engine import ScoringEngine
from app.services.domain_analyzers.base import (
    BaseDomainAnalyzer,
    DomainResult,
    FindingData,
)


class TestGradeMapping:
    """Test grade mapping from score."""

    def test_grade_a(self) -> None:
        assert ScoringEngine.get_grade(800) == "A"
        assert ScoringEngine.get_grade(1000) == "A"

    def test_grade_b(self) -> None:
        assert ScoringEngine.get_grade(600) == "B"
        assert ScoringEngine.get_grade(799) == "B"

    def test_grade_c(self) -> None:
        assert ScoringEngine.get_grade(400) == "C"
        assert ScoringEngine.get_grade(599) == "C"

    def test_grade_d(self) -> None:
        assert ScoringEngine.get_grade(200) == "D"
        assert ScoringEngine.get_grade(399) == "D"

    def test_grade_f(self) -> None:
        assert ScoringEngine.get_grade(0) == "F"
        assert ScoringEngine.get_grade(199) == "F"


class TestSizeNormalization:
    """Test size normalization factors."""

    def test_micro(self) -> None:
        assert ScoringEngine.get_size_factor(5) == 1.15

    def test_pme(self) -> None:
        assert ScoringEngine.get_size_factor(100) == 1.10

    def test_eti(self) -> None:
        assert ScoringEngine.get_size_factor(1000) == 1.0

    def test_grand_groupe(self) -> None:
        assert ScoringEngine.get_size_factor(10000) == 0.90


class TestDomainScoreCalculation:
    """Test domain score calculation from findings."""

    def test_perfect_score_no_findings(self) -> None:
        analyzer = type(
            "TestAnalyzer",
            (BaseDomainAnalyzer,),
            {"analyze": lambda *a, **kw: None},
        )()
        assert analyzer.calculate_score([]) == 100

    def test_deduction_critical(self) -> None:
        analyzer = type(
            "TestAnalyzer",
            (BaseDomainAnalyzer,),
            {"analyze": lambda *a, **kw: None},
        )()
        findings = [
            FindingData(
                domain="D1", title="Test", description="",
                severity="critical",
            ),
        ]
        assert analyzer.calculate_score(findings) == 70

    def test_multiple_findings(self) -> None:
        analyzer = type(
            "TestAnalyzer",
            (BaseDomainAnalyzer,),
            {"analyze": lambda *a, **kw: None},
        )()
        findings = [
            FindingData(domain="D1", title="A", description="", severity="high"),
            FindingData(domain="D1", title="B", description="", severity="medium"),
            FindingData(domain="D1", title="C", description="", severity="low"),
        ]
        # 100 - 20 - 10 - 5 = 65
        assert analyzer.calculate_score(findings) == 65

    def test_score_floors_at_zero(self) -> None:
        analyzer = type(
            "TestAnalyzer",
            (BaseDomainAnalyzer,),
            {"analyze": lambda *a, **kw: None},
        )()
        findings = [
            FindingData(domain="D1", title=f"F{i}", description="", severity="critical")
            for i in range(5)
        ]
        assert analyzer.calculate_score(findings) == 0


class TestDomainGrade:
    """Test domain score to grade mapping."""

    def test_grade_a(self) -> None:
        assert BaseDomainAnalyzer.score_to_grade(80) == "A"
        assert BaseDomainAnalyzer.score_to_grade(100) == "A"

    def test_grade_e(self) -> None:
        assert BaseDomainAnalyzer.score_to_grade(0) == "E"
        assert BaseDomainAnalyzer.score_to_grade(19) == "E"


@pytest.mark.asyncio
class TestScoringEngine:
    """Integration tests for the scoring engine."""

    async def test_score_vendor_empty_data(self) -> None:
        engine = ScoringEngine()
        result = await engine.score_vendor(
            vendor_id="test-vendor-1",
            raw_data={"domain": "example.com"},
        )
        assert "global_score" in result
        assert "grade" in result
        assert "domain_scores" in result
        assert 0 <= result["global_score"] <= 1000
        assert result["grade"] in ("A", "B", "C", "D", "F")

    async def test_score_vendor_with_size_normalization(self) -> None:
        engine = ScoringEngine()
        micro = await engine.score_vendor(
            "v1", {"domain": "micro.fr"}, employee_count=5
        )
        grand = await engine.score_vendor(
            "v2", {"domain": "grand.fr"}, employee_count=10000
        )
        # Micro should have higher score due to +15% tolerance
        assert micro["global_score"] >= grand["global_score"]
