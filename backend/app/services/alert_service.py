"""Alert service — threshold-based alerting with multi-channel dispatch."""

import logging
from typing import Any

logger = logging.getLogger("mh_cyberscore.services.alert")

SCORE_DROP_THRESHOLD = 100
GRADE_ORDER = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


class AlertService:
    """Service for detecting and dispatching alerts."""

    async def check_score_drop(
        self,
        vendor_id: str,
        old_score: int,
        new_score: int,
    ) -> list[dict[str, Any]]:
        """Check if a score drop exceeds the threshold."""
        alerts: list[dict[str, Any]] = []
        drop = old_score - new_score
        if drop > SCORE_DROP_THRESHOLD:
            alerts.append({
                "vendor_id": vendor_id,
                "type": "score_drop",
                "severity": "high",
                "title": f"Chute de score: -{drop} points",
                "description": f"Score passé de {old_score} à {new_score}.",
            })
        return alerts

    async def check_grade_change(
        self,
        vendor_id: str,
        old_grade: str,
        new_grade: str,
    ) -> list[dict[str, Any]]:
        """Check for grade degradation."""
        alerts: list[dict[str, Any]] = []
        if GRADE_ORDER.get(new_grade, 0) < GRADE_ORDER.get(old_grade, 0):
            alerts.append({
                "vendor_id": vendor_id,
                "type": "grade_change",
                "severity": "high",
                "title": f"Dégradation: {old_grade} → {new_grade}",
            })
        return alerts

    async def check_critical_findings(
        self,
        vendor_id: str,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate alerts for critical/high findings."""
        alerts: list[dict[str, Any]] = []
        for f in findings:
            if f.get("severity") in ("critical", "high"):
                alerts.append({
                    "vendor_id": vendor_id,
                    "type": "critical_finding",
                    "severity": f["severity"],
                    "title": f.get("title", "Finding critique"),
                })
        return alerts
