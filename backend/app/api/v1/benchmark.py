"""Benchmark endpoints: sector comparison for vendors and portfolio."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.services.benchmark_service import BenchmarkService

router = APIRouter(prefix="/benchmark", tags=["benchmark"])

_benchmark_service = BenchmarkService()


@router.get("/sectors")
async def list_sectors(
    _current_user: object = Depends(get_current_user),
) -> dict:
    """List available benchmark sectors with summary stats."""
    return {"sectors": _benchmark_service.get_sectors()}


@router.get("/portfolio")
async def portfolio_benchmark(
    sector: str = Query(..., pattern=r"^(assurance|mutuelle|sante|banque|industrie)$"),
    _current_user: object = Depends(get_current_user),
) -> dict:
    """Compare portfolio averages against a sector benchmark.

    Uses mock portfolio data for now; in production this aggregates
    from the scoring database.
    """
    # In production: aggregate from DB
    portfolio_avg_score = 580
    portfolio_domain_avgs = {
        "D1": 62.0, "D2": 65.0, "D3": 58.0, "D4": 63.0,
        "D5": 52.0, "D6": 68.0, "D7": 50.0, "D8": 72.0,
    }

    result = _benchmark_service.compare_portfolio(
        portfolio_avg_score=portfolio_avg_score,
        portfolio_domain_avgs=portfolio_domain_avgs,
        sector=sector,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown sector: {sector}",
        )
    return result


@router.get("/vendors/{vendor_id}")
async def vendor_benchmark(
    vendor_id: str,
    sector: str = Query(..., pattern=r"^(assurance|mutuelle|sante|banque|industrie)$"),
    _current_user: object = Depends(get_current_user),
) -> dict:
    """Compare a vendor's scores against a sector benchmark.

    Uses mock vendor data for now; in production this loads
    from the scoring database.
    """
    # In production: load vendor scores from DB
    vendor_score = 640
    vendor_domain_scores = {
        "D1": 70, "D2": 72, "D3": 65, "D4": 68,
        "D5": 58, "D6": 74, "D7": 55, "D8": 76,
    }

    result = _benchmark_service.compare_vendor(
        vendor_score=vendor_score,
        vendor_domain_scores=vendor_domain_scores,
        sector=sector,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown sector: {sector}",
        )
    result["vendor_id"] = vendor_id
    return result
