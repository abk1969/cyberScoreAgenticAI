"""M365 Rating Service — orchestrates M365 scans and persists results."""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.m365_rating_agent import M365RatingAgent
from app.models.internal_scoring import InternalFinding, InternalScan

logger = logging.getLogger("mh_cyberscore.services.m365_rating")


class M365RatingService:
    """Service layer for Microsoft 365 security rating."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def scan_tenant(
        self,
        tenant_id: str,
        credentials: dict | None = None,
    ) -> InternalScan:
        """Run an M365 security scan and persist results.

        Args:
            tenant_id: Azure AD tenant ID.
            credentials: Auth credentials.

        Returns:
            The persisted InternalScan object.
        """
        agent = M365RatingAgent()
        result = await agent.execute(
            vendor_id=tenant_id,
            tenant_id=tenant_id,
            credentials=credentials or {},
        )

        scan = InternalScan(
            scan_type="m365",
            target=tenant_id,
            score=result.data.get("global_score", 0),
            grade=result.data.get("grade", "F"),
            findings_count=result.data.get("findings_count", 0),
            scan_data=result.data,
        )
        self.db.add(scan)
        await self.db.flush()

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
        """Get the latest M365 scan score.

        Args:
            target: Optional filter by tenant ID.

        Returns:
            Dict with score data or empty dict.
        """
        query = (
            select(InternalScan)
            .where(InternalScan.scan_type == "m365")
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

    async def get_findings(
        self, target: str | None = None
    ) -> list[dict[str, Any]]:
        """Get findings from the latest M365 scan.

        Args:
            target: Optional filter by tenant ID.

        Returns:
            List of finding dicts.
        """
        query = (
            select(InternalScan)
            .where(InternalScan.scan_type == "m365")
            .order_by(InternalScan.created_at.desc())
            .limit(1)
        )
        if target:
            query = query.where(InternalScan.target == target)

        result = await self.db.execute(query)
        scan = result.scalar_one_or_none()
        if not scan:
            return []

        findings_result = await self.db.execute(
            select(InternalFinding)
            .where(InternalFinding.scan_id == scan.id)
            .order_by(InternalFinding.detected_at.desc())
        )
        findings = findings_result.scalars().all()
        return [
            {
                "id": f.id,
                "scan_id": f.scan_id,
                "category": f.category,
                "title": f.title,
                "description": f.description,
                "severity": f.severity,
                "recommendation": f.recommendation,
                "status": f.status,
                "detected_at": f.detected_at.isoformat() if f.detected_at else None,
            }
            for f in findings
        ]
