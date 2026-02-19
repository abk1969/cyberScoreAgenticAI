"""Alert Agent — detects anomalies and dispatches multi-channel alerts.

Monitors for: score drops, grade degradation, critical findings,
trend anomalies. Dispatches via email, webhook (Slack/Teams),
and ServiceNow ticket creation.
"""

import logging
import time
from typing import Any

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.celery_app import celery_app

logger = logging.getLogger("mh_cyberscore.agents.alert")

SCORE_DROP_THRESHOLD = 50
CRITICAL_SEVERITIES = {"critical", "high"}


class AlertAgent(BaseAgent):
    """Anomaly detection and multi-channel alert dispatch."""

    def __init__(self) -> None:
        super().__init__(name="alert")

    async def execute(self, vendor_id: str, **kwargs: Any) -> AgentResult:
        """Check for anomalies and generate alerts.

        Args:
            vendor_id: Vendor UUID.
            **kwargs: old_score, new_score, findings.

        Returns:
            AgentResult with generated alerts.
        """
        start = time.monotonic()
        alerts: list[dict[str, Any]] = []
        old_score = kwargs.get("old_score", 0)
        new_score = kwargs.get("new_score", 0)
        findings = kwargs.get("findings", [])

        # Check score drop
        if old_score - new_score > SCORE_DROP_THRESHOLD:
            alerts.append({
                "type": "score_drop",
                "severity": "high",
                "title": f"Chute de score significative: {old_score} → {new_score}",
                "description": (
                    f"Le fournisseur a perdu {old_score - new_score} points. "
                    "Vérification immédiate recommandée."
                ),
            })

        # Check grade degradation
        old_grade = self._score_to_grade(old_score)
        new_grade = self._score_to_grade(new_score)
        if old_grade != new_grade and old_score > new_score:
            alerts.append({
                "type": "grade_change",
                "severity": "high",
                "title": f"Dégradation de grade: {old_grade} → {new_grade}",
                "description": (
                    f"Le fournisseur est passé du grade {old_grade} "
                    f"au grade {new_grade}."
                ),
            })

        # Check critical findings
        for finding in findings:
            severity = finding.get("severity", "info")
            if severity in CRITICAL_SEVERITIES:
                alerts.append({
                    "type": "critical_finding",
                    "severity": severity,
                    "title": f"Finding {severity}: {finding.get('title', '')}",
                    "description": finding.get("description", ""),
                })

        duration = time.monotonic() - start
        return AgentResult(
            agent_name=self.name,
            vendor_id=vendor_id,
            success=True,
            data={"alerts": alerts, "alert_count": len(alerts)},
            duration_seconds=round(duration, 2),
        )

    @staticmethod
    def _score_to_grade(score: int) -> str:
        """Map score to grade."""
        if score >= 800:
            return "A"
        if score >= 600:
            return "B"
        if score >= 400:
            return "C"
        if score >= 200:
            return "D"
        return "F"

    async def dispatch_email(
        self, alert: dict[str, Any], recipients: list[str]
    ) -> None:
        """Send alert via email (SMTP).

        Uses Python's smtplib to send email alerts. Requires SMTP
        configuration in environment variables.
        """
        import smtplib
        from email.message import EmailMessage

        from app.config import settings

        msg = EmailMessage()
        msg["Subject"] = f"[MH-CyberScore] {alert.get('severity', 'info').upper()}: {alert.get('title', 'Alerte')}"
        msg["From"] = getattr(settings, "smtp_from", "noreply@malakoffhumanis.com")
        msg["To"] = ", ".join(recipients)
        msg.set_content(alert.get("description", ""))

        smtp_host = getattr(settings, "smtp_host", "")
        smtp_port = getattr(settings, "smtp_port", 587)
        if smtp_host:
            try:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    server.ehlo()
                    server.starttls()
                    server.send_message(msg)
                self.logger.info("Email alert dispatched to %s", recipients)
            except Exception as exc:
                self.logger.warning("Email dispatch failed: %s", exc)
        else:
            self.logger.warning("SMTP not configured, email alert skipped")

    async def dispatch_webhook(
        self, alert: dict[str, Any], webhook_url: str
    ) -> None:
        """Send alert via webhook (Slack/Teams compatible JSON format)."""
        import httpx

        payload = {
            "text": f"*[{alert.get('severity', 'info').upper()}]* {alert.get('title', '')}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*{alert.get('title', '')}*\n"
                            f"Severity: {alert.get('severity', 'info')}\n"
                            f"Type: {alert.get('type', 'unknown')}\n\n"
                            f"{alert.get('description', '')}"
                        ),
                    },
                },
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(webhook_url, json=payload)
                resp.raise_for_status()
            self.logger.info("Webhook alert dispatched to %s", webhook_url)
        except Exception as exc:
            self.logger.warning("Webhook dispatch failed: %s", exc)

    async def create_servicenow_ticket(
        self, alert: dict[str, Any]
    ) -> str | None:
        """Create a ServiceNow incident ticket via REST API.

        Requires servicenow_instance, servicenow_user, servicenow_password
        in settings.
        """
        import httpx

        from app.config import settings

        instance = getattr(settings, "servicenow_instance", "")
        user = getattr(settings, "servicenow_user", "")
        password = getattr(settings, "servicenow_password", "")

        if not instance:
            self.logger.warning("ServiceNow not configured, ticket creation skipped")
            return None

        url = f"https://{instance}.service-now.com/api/now/table/incident"
        payload = {
            "short_description": alert.get("title", "MH-CyberScore Alert"),
            "description": alert.get("description", ""),
            "urgency": "1" if alert.get("severity") == "critical" else "2",
            "impact": "2",
            "category": "Security",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    url, json=payload,
                    auth=(user, password),
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                ticket = resp.json().get("result", {})
                ticket_number = ticket.get("number", "")
                self.logger.info("ServiceNow ticket created: %s", ticket_number)
                return ticket_number
        except Exception as exc:
            self.logger.warning("ServiceNow ticket creation failed: %s", exc)
            return None


@celery_app.task(name="app.agents.alert_agent.check_anomalies")
def check_anomalies(
    vendor_id: str,
    old_score: int = 0,
    new_score: int = 0,
    findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Celery task: check for anomalies and generate alerts."""
    import asyncio

    agent = AlertAgent()
    result = asyncio.run(
        agent.execute(
            vendor_id,
            old_score=old_score,
            new_score=new_score,
            findings=findings or [],
        )
    )
    return result.data
