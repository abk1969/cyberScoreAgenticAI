"""AD Rating Service — orchestrates AD scans and persists results."""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.ad_rating_agent import ADRatingAgent
from app.models.internal_scoring import InternalFinding, InternalScan

logger = logging.getLogger("cyberscore.services.ad_rating")


class ADRatingService:
    """Service layer for Active Directory security rating."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def scan_domain(
        self,
        domain_controller: str,
        credentials: dict | None = None,
        threshold_dormant_days: int = 90,
    ) -> InternalScan:
        """Run an AD security scan and persist results.

        Args:
            domain_controller: DC hostname or IP.
            credentials: Auth credentials.
            threshold_dormant_days: Dormant account threshold.

        Returns:
            The persisted InternalScan object.
        """
        agent = ADRatingAgent()
        result = await agent.execute(
            vendor_id=domain_controller,
            domain_controller=domain_controller,
            credentials=credentials or {},
            threshold_dormant_days=threshold_dormant_days,
        )

        scan = InternalScan(
            scan_type="ad",
            target=domain_controller,
            score=result.data.get("global_score", 0),
            grade=result.data.get("grade", "F"),
            findings_count=result.data.get("findings_count", 0),
            scan_data=result.data,
        )
        self.db.add(scan)
        await self.db.flush()

        # Persist individual findings
        for f in result.data.get("findings", []):
            finding = InternalFinding(
                scan_id=scan.id,
                category=f.get("category", "unknown"),
                title=f.get("title", ""),
                description=f.get("description"),
                severity=f.get("severity", "info"),
                recommendation=f.get("recommendation"),
            )
            self.db.add(finding)

        await self.db.flush()
        return scan

    async def get_score(self, target: str | None = None) -> dict[str, Any]:
        """Get the latest AD scan score.

        Args:
            target: Optional filter by domain controller.

        Returns:
            Dict with score data or empty dict.
        """
        query = (
            select(InternalScan)
            .where(InternalScan.scan_type == "ad")
            .order_by(InternalScan.created_at.desc())
            .limit(1)
        )
        if target:
            query = query.where(InternalScan.target == target)

        result = await self.db.execute(query)
        scan = result.scalar_one_or_none()
        if not scan:
            return {}
        return {
            "id": scan.id,
            "score": scan.score,
            "grade": scan.grade,
            "findings_count": scan.findings_count,
            "category_scores": scan.scan_data.get("category_scores", {}),
            "created_at": scan.created_at.isoformat() if scan.created_at else None,
        }

    async def get_history(
        self, target: str | None = None, limit: int = 30
    ) -> list[dict[str, Any]]:
        """Get AD scan history.

        Args:
            target: Optional filter by domain controller.
            limit: Max number of results.

        Returns:
            List of historical scan summaries.
        """
        query = (
            select(InternalScan)
            .where(InternalScan.scan_type == "ad")
            .order_by(InternalScan.created_at.desc())
            .limit(limit)
        )
        if target:
            query = query.where(InternalScan.target == target)

        result = await self.db.execute(query)
        scans = result.scalars().all()
        return [
            {
                "id": s.id,
                "score": s.score,
                "grade": s.grade,
                "findings_count": s.findings_count,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in scans
        ]

    async def compare_timeshift(
        self, scan1_id: str, scan2_id: str
    ) -> dict[str, Any]:
        """Compare two AD scans for timeshift analysis.

        Args:
            scan1_id: First (older) scan ID.
            scan2_id: Second (newer) scan ID.

        Returns:
            Comparison data with score delta and finding changes.
        """
        result1 = await self.db.execute(
            select(InternalScan).where(InternalScan.id == scan1_id)
        )
        result2 = await self.db.execute(
            select(InternalScan).where(InternalScan.id == scan2_id)
        )
        scan1 = result1.scalar_one_or_none()
        scan2 = result2.scalar_one_or_none()

        if not scan1 or not scan2:
            return {"error": "One or both scans not found"}

        cat1 = scan1.scan_data.get("category_scores", {})
        cat2 = scan2.scan_data.get("category_scores", {})

        category_deltas = {}
        for cat in set(list(cat1.keys()) + list(cat2.keys())):
            old_val = cat1.get(cat, 0)
            new_val = cat2.get(cat, 0)
            category_deltas[cat] = {
                "old": old_val,
                "new": new_val,
                "delta": new_val - old_val,
            }

        return {
            "scan1": {"id": scan1.id, "score": scan1.score, "grade": scan1.grade},
            "scan2": {"id": scan2.id, "score": scan2.score, "grade": scan2.grade},
            "score_delta": scan2.score - scan1.score,
            "findings_delta": scan2.findings_count - scan1.findings_count,
            "category_deltas": category_deltas,
        }
