"""Splunk HEC integration — push scoring events and alerts."""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("cyberscore.integrations.splunk")


class SplunkService:
    """Push events to Splunk via HTTP Event Collector."""

    def __init__(self) -> None:
        self.hec_url = settings.splunk_hec_url
        self.hec_token = settings.splunk_hec_token

    @property
    def configured(self) -> bool:
        return bool(self.hec_url and self.hec_token)

    async def _post_event(self, event: dict[str, Any]) -> bool:
        if not self.configured:
            logger.warning("Splunk HEC not configured, skipping event push")
            return False

        url = f"{self.hec_url.rstrip('/')}/services/collector/event"
        payload = {"event": event, "sourcetype": "cyberscore"}

        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Splunk {self.hec_token}"},
                )
                resp.raise_for_status()
            logger.info("Splunk event pushed: %s", event.get("event_type", "unknown"))
            return True
        except Exception as exc:
            logger.warning("Splunk HEC push failed: %s", exc)
            return False

    async def push_scoring_event(
        self, vendor_id: str, score: int, grade: str
    ) -> bool:
        return await self._post_event({
            "event_type": "scoring",
            "vendor_id": vendor_id,
            "score": score,
            "grade": grade,
        })

    async def push_alert_event(self, alert: dict[str, Any]) -> bool:
        return await self._post_event({
            "event_type": "alert",
            "severity": alert.get("severity", "info"),
            "title": alert.get("title", ""),
            "description": alert.get("description", ""),
        })

    async def test_connection(self) -> dict[str, Any]:
        if not self.configured:
            return {"success": False, "message": "Splunk HEC not configured"}
        try:
            url = f"{self.hec_url.rstrip('/')}/services/collector/event"
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                resp = await client.post(
                    url,
                    json={"event": {"test": True}},
                    headers={"Authorization": f"Splunk {self.hec_token}"},
                )
                resp.raise_for_status()
            return {"success": True, "message": "Splunk HEC connection OK"}
        except Exception as exc:
            return {"success": False, "message": str(exc)}
