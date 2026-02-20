"""Benchmark Service — sector-level benchmark comparison.

Provides reference data for French insurance/mutual/health/banking/industry
sectors and compares vendor or portfolio scores against sector averages.
"""

import logging
from typing import Any

logger = logging.getLogger("cyberscore.services.benchmark")

# Reference benchmark data per sector (percentiles & averages per domain).
# Values represent typical scores observed across French entities in each sector.
SECTOR_BENCHMARKS: dict[str, dict[str, Any]] = {
    "assurance": {
        "label": "Assurance",
        "global_avg": 620,
        "global_p25": 480,
        "global_p50": 620,
        "global_p75": 740,
        "global_p90": 820,
        "domain_averages": {
            "D1": 68, "D2": 72, "D3": 65, "D4": 70,
            "D5": 60, "D6": 75, "D7": 55, "D8": 78,
        },
    },
    "mutuelle": {
        "label": "Mutuelle",
        "global_avg": 540,
        "global_p25": 400,
        "global_p50": 540,
        "global_p75": 660,
        "global_p90": 760,
        "domain_averages": {
            "D1": 58, "D2": 62, "D3": 55, "D4": 60,
            "D5": 50, "D6": 65, "D7": 48, "D8": 70,
        },
    },
    "sante": {
        "label": "Sante",
        "global_avg": 480,
        "global_p25": 350,
        "global_p50": 480,
        "global_p75": 600,
        "global_p90": 720,
        "domain_averages": {
            "D1": 52, "D2": 55, "D3": 48, "D4": 54,
            "D5": 45, "D6": 58, "D7": 42, "D8": 65,
        },
    },
    "banque": {
        "label": "Banque",
        "global_avg": 680,
        "global_p25": 540,
        "global_p50": 680,
        "global_p75": 790,
        "global_p90": 860,
        "domain_averages": {
            "D1": 75, "D2": 78, "D3": 72, "D4": 76,
            "D5": 68, "D6": 80, "D7": 62, "D8": 82,
        },
    },
    "industrie": {
        "label": "Industrie",
        "global_avg": 420,
        "global_p25": 300,
        "global_p50": 420,
        "global_p75": 550,
        "global_p90": 680,
        "domain_averages": {
            "D1": 48, "D2": 50, "D3": 42, "D4": 46,
            "D5": 38, "D6": 52, "D7": 35, "D8": 55,
        },
    },
}

DOMAIN_NAMES = {
    "D1": "Securite Reseau",
    "D2": "Securite DNS",
    "D3": "Securite Web",
    "D4": "Securite Email",
    "D5": "Cadence Correctifs",
    "D6": "Reputation IP",
    "D7": "Fuites & Exposition",
    "D8": "Presence Reglementaire",
}


class BenchmarkService:
    """Sector benchmark comparison service."""

    def get_sectors(self) -> list[dict[str, Any]]:
        """Return available sectors with summary stats."""
        return [
            {
                "key": key,
                "label": data["label"],
                "global_avg": data["global_avg"],
                "global_p50": data["global_p50"],
            }
            for key, data in SECTOR_BENCHMARKS.items()
        ]

    def get_sector_benchmark(self, sector: str) -> dict[str, Any] | None:
        """Return full benchmark data for a sector.

        Args:
            sector: Sector key (assurance, mutuelle, sante, banque, industrie).

        Returns:
            Benchmark dict with percentiles and domain averages, or None.
        """
        bench = SECTOR_BENCHMARKS.get(sector)
        if bench is None:
            return None
        return {
            **bench,
            "sector": sector,
            "domains": [
                {
                    "code": code,
                    "name": DOMAIN_NAMES[code],
                    "sector_avg": avg,
                }
                for code, avg in bench["domain_averages"].items()
            ],
        }

    def compare_vendor(
        self,
        vendor_score: int,
        vendor_domain_scores: dict[str, int],
        sector: str,
    ) -> dict[str, Any] | None:
        """Compare a vendor's scores against sector benchmark.

        Args:
            vendor_score: Vendor's global score (0-1000).
            vendor_domain_scores: Dict of domain code -> score (0-100).
            sector: Sector key.

        Returns:
            Comparison data with percentile position and domain deltas.
        """
        bench = SECTOR_BENCHMARKS.get(sector)
        if bench is None:
            return None

        # Determine percentile bracket
        if vendor_score >= bench["global_p90"]:
            percentile = "top_10"
            percentile_label = "Top 10%"
        elif vendor_score >= bench["global_p75"]:
            percentile = "top_25"
            percentile_label = "Top 25%"
        elif vendor_score >= bench["global_p50"]:
            percentile = "top_50"
            percentile_label = "Top 50%"
        elif vendor_score >= bench["global_p25"]:
            percentile = "bottom_50"
            percentile_label = "Bottom 50%"
        else:
            percentile = "bottom_25"
            percentile_label = "Bottom 25%"

        domain_comparison = []
        for code, sector_avg in bench["domain_averages"].items():
            vendor_ds = vendor_domain_scores.get(code, 50)
            domain_comparison.append({
                "code": code,
                "name": DOMAIN_NAMES[code],
                "vendor_score": vendor_ds,
                "sector_avg": sector_avg,
                "delta": vendor_ds - sector_avg,
                "status": "above" if vendor_ds >= sector_avg else "below",
            })

        return {
            "sector": sector,
            "sector_label": bench["label"],
            "vendor_score": vendor_score,
            "sector_avg": bench["global_avg"],
            "delta": vendor_score - bench["global_avg"],
            "percentile": percentile,
            "percentile_label": percentile_label,
            "domain_comparison": domain_comparison,
        }

    def compare_portfolio(
        self,
        portfolio_avg_score: int,
        portfolio_domain_avgs: dict[str, float],
        sector: str,
    ) -> dict[str, Any] | None:
        """Compare portfolio average against sector benchmark.

        Args:
            portfolio_avg_score: Portfolio average global score.
            portfolio_domain_avgs: Dict of domain code -> avg score.
            sector: Sector key.

        Returns:
            Portfolio comparison data.
        """
        bench = SECTOR_BENCHMARKS.get(sector)
        if bench is None:
            return None

        domain_comparison = []
        for code, sector_avg in bench["domain_averages"].items():
            portfolio_ds = portfolio_domain_avgs.get(code, 50.0)
            domain_comparison.append({
                "code": code,
                "name": DOMAIN_NAMES[code],
                "portfolio_avg": round(portfolio_ds, 1),
                "sector_avg": sector_avg,
                "delta": round(portfolio_ds - sector_avg, 1),
                "status": "above" if portfolio_ds >= sector_avg else "below",
            })

        return {
            "sector": sector,
            "sector_label": bench["label"],
            "portfolio_avg_score": portfolio_avg_score,
            "sector_avg": bench["global_avg"],
            "delta": portfolio_avg_score - bench["global_avg"],
            "sector_p25": bench["global_p25"],
            "sector_p50": bench["global_p50"],
            "sector_p75": bench["global_p75"],
            "sector_p90": bench["global_p90"],
            "domain_comparison": domain_comparison,
        }
