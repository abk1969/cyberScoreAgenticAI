"""Power BI integration service — tabular dataset with OData-like query support."""

import logging
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scoring import Finding, VendorScore
from app.models.vendor import Vendor

logger = logging.getLogger("mh_cyberscore.services.powerbi")


class PowerBIService:
    """Provides scoring data in Power BI-compatible tabular format with OData-like queries."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_dataset(
        self,
        filter_expr: str | None = None,
        select_fields: str | None = None,
        orderby: str | None = None,
        top: int | None = None,
    ) -> dict[str, Any]:
        """Return all scoring data in a Power BI-compatible tabular format.

        Supports OData-like query parameters:
            ?$filter=grade eq 'A'
            ?$select=vendor_name,global_score,grade
            ?$orderby=global_score desc
            ?$top=50

        Args:
            filter_expr: OData-like filter string.
            select_fields: Comma-separated field names.
            orderby: Field and direction (asc/desc).
            top: Limit number of rows.

        Returns:
            Dict with 'columns', 'rows', and 'metadata'.
        """
        # Fetch all active vendors with their latest score
        vendor_q = select(Vendor).where(Vendor.status == "active")
        vendor_result = await self._db.execute(vendor_q)
        vendors = vendor_result.scalars().all()

        score_q = select(VendorScore).order_by(VendorScore.scanned_at.desc())
        score_result = await self._db.execute(score_q)
        scores = score_result.scalars().all()

        # Map latest score per vendor
        score_map: dict[str, VendorScore] = {}
        for s in scores:
            if s.vendor_id not in score_map:
                score_map[s.vendor_id] = s

        # Count findings per vendor
        finding_q = select(Finding).where(Finding.status == "open")
        finding_result = await self._db.execute(finding_q)
        findings = finding_result.scalars().all()
        finding_counts: dict[str, dict[str, int]] = {}
        for f in findings:
            counts = finding_counts.setdefault(f.vendor_id, {
                "critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0,
            })
            counts[f.severity] = counts.get(f.severity, 0) + 1
            counts["total"] += 1

        # Build tabular rows
        all_rows: list[dict[str, Any]] = []
        for v in vendors:
            sc = score_map.get(v.id)
            fc = finding_counts.get(v.id, {})
            domain_scores = sc.domain_scores if sc else {}

            row: dict[str, Any] = {
                "vendor_id": v.id,
                "vendor_name": v.name,
                "domain": v.domain,
                "tier": v.tier,
                "industry": v.industry or "",
                "country": v.country or "",
                "status": v.status,
                "global_score": sc.global_score if sc else None,
                "grade": sc.grade if sc else None,
                "scanned_at": sc.scanned_at.isoformat() if sc and sc.scanned_at else None,
                "findings_critical": fc.get("critical", 0),
                "findings_high": fc.get("high", 0),
                "findings_medium": fc.get("medium", 0),
                "findings_low": fc.get("low", 0),
                "findings_total": fc.get("total", 0),
            }
            # Add domain scores as separate columns
            for d_name, d_val in domain_scores.items():
                row[f"score_{d_name}"] = d_val

            all_rows.append(row)

        # Apply OData-like filters
        rows = self._apply_filter(all_rows, filter_expr)
        rows = self._apply_orderby(rows, orderby)
        if top:
            rows = rows[:top]
        rows = self._apply_select(rows, select_fields)

        columns = list(rows[0].keys()) if rows else []

        return {
            "columns": columns,
            "rows": rows,
            "metadata": {
                "total_rows": len(rows),
                "total_vendors": len(vendors),
                "format": "tabular",
                "odata_supported": ["$filter", "$select", "$orderby", "$top"],
            },
        }

    @staticmethod
    def _apply_filter(
        rows: list[dict[str, Any]], filter_expr: str | None
    ) -> list[dict[str, Any]]:
        """Apply a simple OData-like filter expression.

        Supports: field eq 'value', field gt N, field lt N, field ge N, field le N.
        Multiple conditions with 'and'.
        """
        if not filter_expr:
            return rows

        conditions = re.split(r"\s+and\s+", filter_expr, flags=re.IGNORECASE)
        filtered = rows

        for cond in conditions:
            cond = cond.strip()
            match = re.match(
                r"(\w+)\s+(eq|ne|gt|lt|ge|le)\s+['\"]?([^'\"]+)['\"]?",
                cond, re.IGNORECASE,
            )
            if not match:
                continue

            field, op, value = match.group(1), match.group(2).lower(), match.group(3)

            def _matches(row: dict[str, Any], f: str = field, o: str = op, v: str = value) -> bool:
                rv = row.get(f)
                if rv is None:
                    return False
                # Try numeric comparison
                try:
                    rv_num = float(rv)
                    v_num = float(v)
                    ops = {"eq": rv_num == v_num, "ne": rv_num != v_num,
                           "gt": rv_num > v_num, "lt": rv_num < v_num,
                           "ge": rv_num >= v_num, "le": rv_num <= v_num}
                    return ops.get(o, False)
                except (ValueError, TypeError):
                    pass
                # String comparison
                rv_str = str(rv)
                ops_str = {"eq": rv_str == v, "ne": rv_str != v}
                return ops_str.get(o, False)

            filtered = [r for r in filtered if _matches(r)]

        return filtered

    @staticmethod
    def _apply_orderby(
        rows: list[dict[str, Any]], orderby: str | None
    ) -> list[dict[str, Any]]:
        """Apply OData-like $orderby."""
        if not orderby:
            return rows

        parts = orderby.strip().split()
        field = parts[0]
        desc = len(parts) > 1 and parts[1].lower() == "desc"

        return sorted(
            rows,
            key=lambda r: (r.get(field) is None, r.get(field, "")),
            reverse=desc,
        )

    @staticmethod
    def _apply_select(
        rows: list[dict[str, Any]], select_fields: str | None
    ) -> list[dict[str, Any]]:
        """Apply OData-like $select to limit columns."""
        if not select_fields:
            return rows

        fields = [f.strip() for f in select_fields.split(",")]
        return [{k: r.get(k) for k in fields if k in r} for r in rows]
