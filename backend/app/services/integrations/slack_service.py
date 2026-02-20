"""Slack webhook integration — alerts and report notifications via Block Kit."""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("cyberscore.integrations.slack")

SEVERITY_EMOJI = {
    "critical": ":rotating_light:",
    "high": ":warning:",
    "medium": ":large_orange_diamond:",
    "low": ":information_source:",
    "info": ":memo:",
}


class SlackService:
    """Send notifications to Slack via incoming webhooks with Block Kit format."""

    def __init__(self) -> None:
        self.webhook_url = settings.slack_webhook_url

    @property
    def configured(self) -> bool:
        return bool(self.webhook_url)

    async def _post(self, payload: dict[str, Any]) -> bool:
        if not self.configured:
            logger.warning("Slack webhook not configured, skipping notification")
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
            return True
        except Exception as exc:
            logger.warning("Slack notification failed: %s", exc)
            return False

    async def send_alert(self, alert: dict[str, Any]) -> bool:
        severity = alert.get("severity", "info")
        emoji = SEVERITY_EMOJI.get(severity, ":bell:")
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} CyberScore Alert",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
                        {"type": "mrkdwn", "text": f"*Type:*\n{alert.get('type', 'unknown')}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{alert.get('title', '')}*\n{alert.get('description', '')}",
                    },
                },
                {"type": "divider"},
            ],
        }
        result = await self._post(payload)
        if result:
            logger.info("Slack alert sent: %s", alert.get("title", ""))
        return result

    async def send_report_notification(self, report: dict[str, Any]) -> bool:
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":bar_chart: CyberScore Report Available",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*{report.get('title', 'New Report')}*\n"
                            f"Type: {report.get('type', 'N/A')}\n"
                            f"Generated: {report.get('generated_at', 'N/A')}"
                        ),
                    },
                },
                {"type": "divider"},
            ],
        }
        result = await self._post(payload)
        if result:
            logger.info("Slack report notification sent: %s", report.get("title", ""))
        return result

    async def test_connection(self) -> dict[str, Any]:
        if not self.configured:
            return {"success": False, "message": "Slack webhook not configured"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    self.webhook_url,
                    json={"text": "CyberScore connectivity test :white_check_mark:"},
                )
                resp.raise_for_status()
            return {"success": True, "message": "Slack webhook connection OK"}
        except Exception as exc:
            return {"success": False, "message": str(exc)}
