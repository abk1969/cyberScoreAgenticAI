"""Supply Chain service — dependency graph and concentration risk analysis."""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scoring import VendorScore
from app.models.supply_chain import ConcentrationAlert, VendorDependency
from app.models.vendor import Vendor
from app.schemas.supply_chain import (
    ConcentrationRisk,
    ConcentrationRiskResponse,
    GraphData,
    SupplyChainLink,
    SupplyChainNode,
    VendorDependencyResponse,
)

logger = logging.getLogger("mh_cyberscore.services.supply_chain")

CONCENTRATION_THRESHOLD = 0.30


class SupplyChainService:
    """Service for building dependency graphs and calculating concentration risk."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def build_dependency_graph(
        self, vendor_ids: list[str] | None = None
    ) -> GraphData:
        """Build a NetworkX-compatible JSON graph of vendor dependencies.

        Args:
            vendor_ids: Optional filter; if None, includes all vendors.

        Returns:
            GraphData with nodes and links for D3.js rendering.
        """
        # Fetch vendors
        vendor_q = select(Vendor).where(Vendor.status == "active")
        if vendor_ids:
            vendor_q = vendor_q.where(Vendor.id.in_(vendor_ids))
        result = await self._db.execute(vendor_q)
        vendors = result.scalars().all()

        vendor_map = {v.id: v for v in vendors}
        target_ids = list(vendor_map.keys())

        if not target_ids:
            return GraphData(nodes=[], links=[])

        # Fetch dependencies
        dep_q = select(VendorDependency).where(
            VendorDependency.vendor_id.in_(target_ids)
        )
        dep_result = await self._db.execute(dep_q)
        dependencies = dep_result.scalars().all()

        # Fetch latest scores for vendors
        score_q = (
            select(VendorScore)
            .where(VendorScore.vendor_id.in_(target_ids))
            .order_by(VendorScore.scanned_at.desc())
        )
        score_result = await self._db.execute(score_q)
        scores = score_result.scalars().all()
        score_map: dict[str, VendorScore] = {}
        for s in scores:
            if s.vendor_id not in score_map:
                score_map[s.vendor_id] = s

        # Build nodes
        nodes: list[SupplyChainNode] = []
        provider_node_ids: set[str] = set()

        for v in vendors:
            sc = score_map.get(v.id)
            nodes.append(SupplyChainNode(
                id=v.id,
                name=v.name,
                type="vendor",
                tier=v.tier,
                score=sc.global_score if sc else None,
                grade=sc.grade if sc else None,
            ))

        # Build links and provider nodes
        links: list[SupplyChainLink] = []
        for dep in dependencies:
            provider_id = f"provider:{dep.provider_name}"
            if provider_id not in provider_node_ids:
                provider_node_ids.add(provider_id)
                nodes.append(SupplyChainNode(
                    id=provider_id,
                    name=dep.provider_name,
                    type="provider",
                    tier=dep.dependency_tier,
                    provider_type=dep.provider_type,
                ))
            links.append(SupplyChainLink(
                source=dep.vendor_id,
                target=provider_id,
                type="direct" if dep.dependency_tier == 1 else "indirect",
                detected_via=dep.detected_via,
                confidence=dep.confidence,
            ))

        return GraphData(nodes=nodes, links=links)

    async def calculate_concentration_risk(self) -> ConcentrationRiskResponse:
        """Calculate concentration risk across all vendors.

        Groups dependencies by provider and alerts if any provider
        supports > 30% of vendors.

        Returns:
            ConcentrationRiskResponse with risk breakdown.
        """
        # Count total active vendors
        vendor_count_q = select(func.count(Vendor.id)).where(
            Vendor.status == "active"
        )
        vendor_count_result = await self._db.execute(vendor_count_q)
        total_vendors = vendor_count_result.scalar() or 1

        # Group dependencies by provider
        provider_q = (
            select(
                VendorDependency.provider_name,
                func.count(func.distinct(VendorDependency.vendor_id)).label("dep_count"),
            )
            .group_by(VendorDependency.provider_name)
            .order_by(func.count(func.distinct(VendorDependency.vendor_id)).desc())
        )
        provider_result = await self._db.execute(provider_q)
        provider_rows = provider_result.all()

        risks: list[ConcentrationRisk] = []
        for row in provider_rows:
            provider_name = row[0]
            dep_count = row[1]
            pct = dep_count / total_vendors

            if pct >= 0.6:
                risk_level = "critical"
            elif pct >= CONCENTRATION_THRESHOLD:
                risk_level = "high"
            elif pct >= 0.15:
                risk_level = "medium"
            else:
                risk_level = "low"

            risks.append(ConcentrationRisk(
                provider_name=provider_name,
                dependent_count=dep_count,
                percentage=round(pct, 4),
                risk_level=risk_level,
            ))

            # Persist alert if above threshold
            if pct >= CONCENTRATION_THRESHOLD:
                alert = ConcentrationAlert(
                    provider_name=provider_name,
                    dependent_count=dep_count,
                    percentage=round(pct, 4),
                    risk_level=risk_level,
                )
                self._db.add(alert)

        return ConcentrationRiskResponse(
            threshold=CONCENTRATION_THRESHOLD,
            risks=risks,
            total_vendors=total_vendors,
            total_providers=len(provider_rows),
        )

    async def detect_shared_providers(
        self, vendor_ids: list[str]
    ) -> dict[str, list[str]]:
        """Find common infrastructure providers across given vendors.

        Args:
            vendor_ids: List of vendor IDs to compare.

        Returns:
            Dict mapping provider_name to list of vendor IDs that depend on it.
        """
        dep_q = select(VendorDependency).where(
            VendorDependency.vendor_id.in_(vendor_ids)
        )
        result = await self._db.execute(dep_q)
        deps = result.scalars().all()

        provider_vendors: dict[str, set[str]] = {}
        for dep in deps:
            provider_vendors.setdefault(dep.provider_name, set()).add(dep.vendor_id)

        # Only return providers shared by 2+ vendors
        return {
            provider: sorted(vids)
            for provider, vids in provider_vendors.items()
            if len(vids) >= 2
        }

    async def get_vendor_dependencies(
        self, vendor_id: str
    ) -> list[VendorDependencyResponse]:
        """Get all dependencies for a specific vendor.

        Args:
            vendor_id: Vendor UUID.

        Returns:
            List of dependency records.
        """
        q = (
            select(VendorDependency)
            .where(VendorDependency.vendor_id == vendor_id)
            .order_by(VendorDependency.dependency_tier, VendorDependency.provider_name)
        )
        result = await self._db.execute(q)
        deps = result.scalars().all()
        return [VendorDependencyResponse.model_validate(d) for d in deps]

    async def export_graph_json(
        self, vendor_ids: list[str] | None = None
    ) -> dict[str, Any]:
        """Export the full graph as a D3.js-compatible dict.

        Args:
            vendor_ids: Optional filter.

        Returns:
            Dict with 'nodes' and 'links' keys.
        """
        graph = await self.build_dependency_graph(vendor_ids)
        return graph.model_dump()
