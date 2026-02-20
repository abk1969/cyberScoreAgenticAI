"""Microsoft Teams webhook integration — alerts and reports via Adaptive Cards."""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("mh_cyberscore.integrations.teams")

SEVERITY_COLOR = {
    "critical": "attention",
    "high": "warning",
    "medium": "accent",
    "low": "good",
    "info": "default",
}


class TeamsService:
    """Send notifications to Microsoft Teams via incoming webhooks with Adaptive Cards."""

    def __init__(self) -> None:
        self.webhook_url = settings.teams_webhook_url

    @property
    def configured(self) -> bool:
        return bool(self.webhook_url)

    async def _post(self, card: dict[str, Any]) -> bool:
        if not self.configured:
            logger.warning("Teams webhook not configured, skipping notification")
            return False
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": card,
                }
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
            return True
        except Exception as exc:
            logger.warning("Teams notification failed: %s", exc)
            return False

    async def send_alert(self, alert: dict[str, Any]) -> bool:
        severity = alert.get("severity", "info")
        color = SEVERITY_COLOR.get(severity, "default")
        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "large",
                    "weight": "bolder",
                    "text": "MH-CyberScore Alert",
                    "color": color,
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "Severity", "value": severity.upper()},
                        {"title": "Type", "value": alert.get("type", "unknown")},
                    ],
                },
                {
                    "type": "TextBlock",
                    "text": alert.get("title", ""),
                    "weight": "bolder",
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": alert.get("description", ""),
                    "wrap": True,
                },
            ],
        }
        result = await self._post(card)
        if result:
            logger.info("Teams alert sent: %s", alert.get("title", ""))
        return result

    async def send_report_notification(self, report: dict[str, Any]) -> bool:
        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "size": "large",
                    "weight": "bolder",
                    "text": "MH-CyberScore Report Available",
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "Report", "value": report.get("title", "N/A")},
                        {"title": "Type", "value": report.get("type", "N/A")},
                        {"title": "Generated", "value": report.get("generated_at", "N/A")},
                    ],
                },
            ],
        }
        result = await self._post(card)
        if result:
            logger.info("Teams report notification sent: %s", report.get("title", ""))
        return result

    async def test_connection(self) -> dict[str, Any]:
        if not self.configured:
            return {"success": False, "message": "Teams webhook not configured"}
        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "MH-CyberScore connectivity test OK",
                    "color": "good",
                }
            ],
        }
        result = await self._post(card)
        if result:
            return {"success": True, "message": "Teams webhook connection OK"}
        return {"success": False, "message": "Teams webhook POST failed"}
