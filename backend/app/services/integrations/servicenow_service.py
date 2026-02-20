"""ServiceNow integration — incidents, remediation tasks, CMDB sync."""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("cyberscore.integrations.servicenow")


class ServiceNowService:
    """Interact with ServiceNow REST API for incident and CMDB management."""

    def __init__(self) -> None:
        self.instance = settings.servicenow_instance
        self.user = settings.servicenow_user
        self.password = settings.servicenow_password

    @property
    def configured(self) -> bool:
        return bool(self.instance and self.user and self.password)

    @property
    def base_url(self) -> str:
        return f"https://{self.instance}.service-now.com/api/now"

    async def create_incident(self, alert: dict[str, Any]) -> str | None:
        if not self.configured:
            logger.warning("ServiceNow not configured, skipping incident creation")
            return None

        url = f"{self.base_url}/table/incident"
        payload = {
            "short_description": alert.get("title", "CyberScore Alert"),
            "description": alert.get("description", ""),
            "urgency": "1" if alert.get("severity") == "critical" else "2",
            "impact": "2",
            "category": "Security",
            "subcategory": "Vulnerability",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    auth=(self.user, self.password),
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                ticket = resp.json().get("result", {})
                number = ticket.get("number", "")
                logger.info("ServiceNow incident created: %s", number)
                return number
        except Exception as exc:
            logger.warning("ServiceNow incident creation failed: %s", exc)
            return None

    async def create_remediation_task(self, remediation: dict[str, Any]) -> str | None:
        if not self.configured:
            logger.warning("ServiceNow not configured, skipping task creation")
            return None

        url = f"{self.base_url}/table/sc_task"
        payload = {
            "short_description": remediation.get("title", "Remediation Task"),
            "description": remediation.get("description", ""),
            "priority": remediation.get("priority", "3"),
            "assignment_group": remediation.get("assignment_group", ""),
            "due_date": remediation.get("due_date", ""),
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    auth=(self.user, self.password),
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                task = resp.json().get("result", {})
                number = task.get("number", "")
                logger.info("ServiceNow remediation task created: %s", number)
                return number
        except Exception as exc:
            logger.warning("ServiceNow task creation failed: %s", exc)
            return None

    async def sync_cmdb_vendors(self) -> dict[str, Any]:
        if not self.configured:
            return {"success": False, "message": "ServiceNow not configured"}

        url = f"{self.base_url}/table/cmdb_ci_service"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    url,
                    auth=(self.user, self.password),
                    headers={"Accept": "application/json"},
                    params={"sysparm_limit": "500"},
                )
                resp.raise_for_status()
                results = resp.json().get("result", [])
                logger.info("CMDB sync: retrieved %d services", len(results))
                return {"success": True, "count": len(results), "services": results}
        except Exception as exc:
            logger.warning("CMDB sync failed: %s", exc)
            return {"success": False, "message": str(exc)}

    async def test_connection(self) -> dict[str, Any]:
        if not self.configured:
            return {"success": False, "message": "ServiceNow not configured"}
        try:
            url = f"{self.base_url}/table/sys_user?sysparm_limit=1"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    url,
                    auth=(self.user, self.password),
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
            return {"success": True, "message": f"ServiceNow {self.instance} connection OK"}
        except Exception as exc:
            return {"success": False, "message": str(exc)}
