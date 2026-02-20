"""GRC Service — manages security controls, framework mappings, and maturity."""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.grc import FrameworkMapping, MaturityAssessment, SecurityControl

logger = logging.getLogger("cyberscore.services.grc")

FRAMEWORKS = ["iso27001", "dora", "nis2", "hds", "rgpd"]

GRC_DOMAINS = [
    "access_control",
    "network_security",
    "data_protection",
    "incident_management",
    "business_continuity",
    "compliance",
    "physical_security",
    "human_resources",
    "asset_management",
    "cryptography",
    "supplier_management",
    "operations_security",
]


class GRCService:
    """Service layer for GRC/PSSI management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_controls(
        self,
        domain: str | None = None,
        status: str | None = None,
        framework: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get security controls with optional filters.

        Args:
            domain: Filter by control domain.
            status: Filter by implementation status.
            framework: Filter by mapped framework.

        Returns:
            List of control dicts.
        """
        query = (
            select(SecurityControl)
            .options(selectinload(SecurityControl.framework_mappings))
            .order_by(SecurityControl.reference)
        )

        if domain:
            query = query.where(SecurityControl.domain == domain)
        if status:
            query = query.where(SecurityControl.status == status)
        if framework:
            query = query.join(SecurityControl.framework_mappings).where(
                FrameworkMapping.framework == framework
            )

        result = await self.db.execute(query)
        controls = result.scalars().unique().all()

        return [
            {
                "id": c.id,
                "reference": c.reference,
                "title": c.title,
                "description": c.description,
                "domain": c.domain,
                "status": c.status,
                "owner": c.owner,
                "evidence_url": c.evidence_url,
                "last_assessed": c.last_assessed.isoformat() if c.last_assessed else None,
                "frameworks": [m.framework for m in c.framework_mappings],
            }
            for c in controls
        ]

    async def update_control(
        self,
        control_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update a security control.

        Args:
            control_id: Control UUID.
            updates: Fields to update.

        Returns:
            Updated control dict or None if not found.
        """
        result = await self.db.execute(
            select(SecurityControl)
            .options(selectinload(SecurityControl.framework_mappings))
            .where(SecurityControl.id == control_id)
        )
        control = result.scalar_one_or_none()
        if not control:
            return None

        if "status" in updates and updates["status"]:
            control.status = updates["status"]
        if "owner" in updates:
            control.owner = updates["owner"]
        if "evidence_url" in updates:
            control.evidence_url = updates["evidence_url"]

        control.last_assessed = datetime.now(timezone.utc)
        await self.db.flush()

        return {
            "id": control.id,
            "reference": control.reference,
            "title": control.title,
            "description": control.description,
            "domain": control.domain,
            "status": control.status,
            "owner": control.owner,
            "evidence_url": control.evidence_url,
            "last_assessed": control.last_assessed.isoformat(),
            "frameworks": [m.framework for m in control.framework_mappings],
        }

    async def get_maturity_score(self) -> dict[str, Any]:
        """Calculate overall maturity score across all domains.

        Returns:
            Dict with overall score and per-domain breakdown.
        """
        result = await self.db.execute(
            select(
                SecurityControl.domain,
                func.avg(MaturityAssessment.level).label("avg_level"),
                func.count(MaturityAssessment.id).label("assessment_count"),
            )
            .join(
                MaturityAssessment,
                MaturityAssessment.control_id == SecurityControl.id,
            )
            .group_by(SecurityControl.domain)
        )
        rows = result.all()

        domains = {}
        total_score = 0.0
        count = 0
        for row in rows:
            avg = float(row.avg_level) if row.avg_level else 0.0
            domains[row.domain] = {
                "average_level": round(avg, 2),
                "assessment_count": row.assessment_count,
            }
            total_score += avg
            count += 1

        overall = round(total_score / count, 2) if count > 0 else 0.0

        return {
            "overall_maturity": overall,
            "domains": domains,
            "domain_count": count,
        }

    async def get_coverage_by_framework(
        self, framework: str
    ) -> dict[str, Any]:
        """Get implementation coverage for a specific framework.

        Args:
            framework: Framework name (iso27001, dora, nis2, hds, rgpd).

        Returns:
            Coverage summary dict.
        """
        result = await self.db.execute(
            select(SecurityControl.status, func.count(SecurityControl.id))
            .join(
                FrameworkMapping,
                FrameworkMapping.control_id == SecurityControl.id,
            )
            .where(FrameworkMapping.framework == framework)
            .group_by(SecurityControl.status)
        )
        rows = result.all()

        counts = {"implemented": 0, "partial": 0, "not_implemented": 0}
        for row in rows:
            if row[0] in counts:
                counts[row[0]] = row[1]

        total = sum(counts.values())
        coverage_pct = (
            round((counts["implemented"] + counts["partial"] * 0.5) / total * 100, 1)
            if total > 0
            else 0.0
        )

        return {
            "framework": framework,
            "total_controls": total,
            "implemented": counts["implemented"],
            "partial": counts["partial"],
            "not_implemented": counts["not_implemented"],
            "coverage_percent": coverage_pct,
        }

    async def get_heatmap_data(self) -> list[dict[str, Any]]:
        """Generate heatmap data: domain x framework coverage matrix.

        Returns:
            List of heatmap cells.
        """
        result = await self.db.execute(
            select(
                SecurityControl.domain,
                FrameworkMapping.framework,
                SecurityControl.status,
                func.count(SecurityControl.id).label("cnt"),
            )
            .join(
                FrameworkMapping,
                FrameworkMapping.control_id == SecurityControl.id,
            )
            .group_by(
                SecurityControl.domain,
                FrameworkMapping.framework,
                SecurityControl.status,
            )
        )
        rows = result.all()

        # Aggregate by (domain, framework)
        matrix: dict[tuple[str, str], dict[str, int]] = defaultdict(
            lambda: {"implemented": 0, "partial": 0, "not_implemented": 0}
        )
        for row in rows:
            key = (row.domain, row.framework)
            if row.status in matrix[key]:
                matrix[key][row.status] = row.cnt

        cells = []
        for (domain, framework), counts in matrix.items():
            total = sum(counts.values())
            coverage = (
                round(
                    (counts["implemented"] + counts["partial"] * 0.5) / total * 100, 1
                )
                if total > 0
                else 0.0
            )
            if coverage >= 75:
                cell_status = "good"
            elif coverage >= 40:
                cell_status = "warning"
            else:
                cell_status = "critical"

            cells.append({
                "domain": domain,
                "framework": framework,
                "coverage_percent": coverage,
                "status": cell_status,
            })

        return cells

    async def map_control_to_frameworks(
        self,
        control_id: str,
        mappings: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Map a control to one or more framework requirements.

        Args:
            control_id: Security control UUID.
            mappings: List of dicts with 'framework', 'framework_ref', 'description'.

        Returns:
            List of created mapping dicts.
        """
        created = []
        for m in mappings:
            mapping = FrameworkMapping(
                control_id=control_id,
                framework=m["framework"],
                framework_ref=m["framework_ref"],
                description=m.get("description"),
            )
            self.db.add(mapping)
            created.append({
                "framework": mapping.framework,
                "framework_ref": mapping.framework_ref,
            })

        await self.db.flush()
        return created
