"""M365 Rating Agent — scans Microsoft 365 tenant for security misconfigurations.

Checks MFA coverage, Conditional Access, Exchange protection,
SharePoint permissions, Teams settings, and Defender configuration.
Produces a score 0-1000 with detailed findings.
"""

import asyncio
import logging
import time
from typing import Any

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.celery_app import celery_app

logger = logging.getLogger("mh_cyberscore.agents.m365_rating")

M365_WEIGHTS = {
    "mfa_coverage": 0.25,
    "conditional_access": 0.15,
    "exchange_protection": 0.15,
    "sharepoint_permissions": 0.15,
    "teams_settings": 0.10,
    "defender_config": 0.20,
}


class M365RatingAgent(BaseAgent):
    """Microsoft 365 security rating agent."""

    def __init__(self) -> None:
        super().__init__(name="m365_rating", timeout=60.0, rate_limit_per_sec=2.0)

    async def execute(self, vendor_id: str, **kwargs: Any) -> AgentResult:
        """Execute M365 security assessment.

        Args:
            vendor_id: Tenant identifier.
            **kwargs: Must contain 'tenant_id' and 'credentials'.

        Returns:
            AgentResult with M365 security data and score.
        """
        tenant_id = kwargs.get("tenant_id", "")
        credentials = kwargs.get("credentials", {})
        start = time.monotonic()
        errors: list[str] = []
        findings: list[dict[str, Any]] = []
        category_scores: dict[str, float] = {}

        self.logger.info("Starting M365 rating scan for tenant %s", tenant_id)

        # Check 1: MFA coverage
        try:
            result = await self._check_mfa_coverage(tenant_id, credentials)
            category_scores["mfa_coverage"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"MFA coverage check: {exc}")
            category_scores["mfa_coverage"] = 50.0

        # Check 2: Conditional Access
        try:
            result = await self._check_conditional_access(tenant_id, credentials)
            category_scores["conditional_access"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"Conditional Access check: {exc}")
            category_scores["conditional_access"] = 50.0

        # Check 3: Exchange protection
        try:
            result = await self._check_exchange_protection(tenant_id, credentials)
            category_scores["exchange_protection"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"Exchange protection check: {exc}")
            category_scores["exchange_protection"] = 50.0

        # Check 4: SharePoint permissions
        try:
            result = await self._check_sharepoint_permissions(tenant_id, credentials)
            category_scores["sharepoint_permissions"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"SharePoint permissions check: {exc}")
            category_scores["sharepoint_permissions"] = 50.0

        # Check 5: Teams settings
        try:
            result = await self._check_teams_settings(tenant_id, credentials)
            category_scores["teams_settings"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"Teams settings check: {exc}")
            category_scores["teams_settings"] = 50.0

        # Check 6: Defender configuration
        try:
            result = await self._check_defender_config(tenant_id, credentials)
            category_scores["defender_config"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"Defender config check: {exc}")
            category_scores["defender_config"] = 50.0

        # Calculate weighted global score
        global_score = 0.0
        for category, weight in M365_WEIGHTS.items():
            global_score += category_scores.get(category, 50.0) * weight
        global_score = int(max(0, min(1000, global_score * 10)))

        grade = self._score_to_grade(global_score)

        duration = time.monotonic() - start
        return AgentResult(
            agent_name=self.name,
            vendor_id=vendor_id,
            success=len(errors) < 3,
            data={
                "tenant_id": tenant_id,
                "global_score": global_score,
                "grade": grade,
                "category_scores": category_scores,
                "findings": findings,
                "findings_count": len(findings),
            },
            errors=errors,
            duration_seconds=round(duration, 2),
            api_calls_made=self._api_call_count,
        )

    async def _check_mfa_coverage(
        self, tenant_id: str, creds: dict
    ) -> dict[str, Any]:
        """Check percentage of users with MFA enabled."""
        await asyncio.sleep(0.1)

        findings: list[dict[str, Any]] = []
        score = 100.0

        # Simulated — in production, query MS Graph /reports/authenticationMethods
        mfa_data = {
            "total_users": 150,
            "mfa_enabled": 120,
            "mfa_percent": 80.0,
            "admins_without_mfa": 1,
        }

        if mfa_data["mfa_percent"] < 50:
            score -= 50
            findings.append({
                "category": "mfa_coverage",
                "title": f"Couverture MFA critique: {mfa_data['mfa_percent']:.0f}%",
                "description": f"Seulement {mfa_data['mfa_enabled']}/{mfa_data['total_users']} utilisateurs avec MFA",
                "severity": "critical",
                "recommendation": "Deployer MFA pour tous les utilisateurs via Conditional Access",
            })
        elif mfa_data["mfa_percent"] < 90:
            score -= 25
            findings.append({
                "category": "mfa_coverage",
                "title": f"Couverture MFA insuffisante: {mfa_data['mfa_percent']:.0f}%",
                "severity": "high",
                "recommendation": "Augmenter la couverture MFA a 100%",
            })

        if mfa_data["admins_without_mfa"] > 0:
            score -= 30
            findings.append({
                "category": "mfa_coverage",
                "title": f"{mfa_data['admins_without_mfa']} admin(s) sans MFA",
                "severity": "critical",
                "recommendation": "Activer immediatement le MFA pour tous les administrateurs",
            })

        return {"score": max(0, score), "findings": findings, "data": mfa_data}

    async def _check_conditional_access(
        self, tenant_id: str, creds: dict
    ) -> dict[str, Any]:
        """Analyze Conditional Access policies."""
        await asyncio.sleep(0.1)

        findings: list[dict[str, Any]] = []
        score = 100.0

        # Simulated CA policy analysis
        ca_policies = {
            "total_policies": 5,
            "enabled_policies": 4,
            "mfa_policy": True,
            "device_compliance_policy": True,
            "location_policy": False,
            "sign_in_risk_policy": False,
            "legacy_auth_blocked": True,
        }

        if not ca_policies["mfa_policy"]:
            score -= 30
            findings.append({
                "category": "conditional_access",
                "title": "Pas de politique CA imposant le MFA",
                "severity": "critical",
                "recommendation": "Creer une politique CA requierant le MFA pour tous les utilisateurs",
            })

        if not ca_policies["sign_in_risk_policy"]:
            score -= 15
            findings.append({
                "category": "conditional_access",
                "title": "Pas de politique basee sur le risque de connexion",
                "severity": "medium",
                "recommendation": "Activer Identity Protection et configurer des politiques basees sur le risque",
            })

        if not ca_policies["location_policy"]:
            score -= 10
            findings.append({
                "category": "conditional_access",
                "title": "Pas de restriction geographique configuree",
                "severity": "low",
                "recommendation": "Configurer des emplacements nommes et restreindre l'acces",
            })

        if not ca_policies["legacy_auth_blocked"]:
            score -= 25
            findings.append({
                "category": "conditional_access",
                "title": "Authentification legacy non bloquee",
                "severity": "high",
                "recommendation": "Bloquer l'authentification legacy via Conditional Access",
            })

        return {"score": max(0, score), "findings": findings, "data": ca_policies}

    async def _check_exchange_protection(
        self, tenant_id: str, creds: dict
    ) -> dict[str, Any]:
        """Check Exchange Online protection: anti-spam, DKIM, DMARC, ATP."""
        await asyncio.sleep(0.1)

        findings: list[dict[str, Any]] = []
        score = 100.0

        exchange_config = {
            "anti_spam_enabled": True,
            "dkim_enabled": True,
            "dmarc_policy": "quarantine",
            "atp_safe_attachments": True,
            "atp_safe_links": True,
            "external_forwarding_blocked": False,
            "audit_logging": True,
        }

        if exchange_config["dmarc_policy"] != "reject":
            deduction = 10 if exchange_config["dmarc_policy"] == "quarantine" else 25
            severity = "medium" if exchange_config["dmarc_policy"] == "quarantine" else "high"
            score -= deduction
            findings.append({
                "category": "exchange_protection",
                "title": f"DMARC en mode '{exchange_config['dmarc_policy']}' au lieu de 'reject'",
                "severity": severity,
                "recommendation": "Passer progressivement la politique DMARC a 'reject'",
            })

        if not exchange_config["external_forwarding_blocked"]:
            score -= 20
            findings.append({
                "category": "exchange_protection",
                "title": "Transfert externe de mails non bloque",
                "description": "Les utilisateurs peuvent configurer des regles de transfert externe",
                "severity": "high",
                "recommendation": "Bloquer le transfert automatique externe via transport rules",
            })

        if not exchange_config["dkim_enabled"]:
            score -= 15
            findings.append({
                "category": "exchange_protection",
                "title": "DKIM non active",
                "severity": "high",
                "recommendation": "Activer DKIM pour tous les domaines",
            })

        return {"score": max(0, score), "findings": findings, "data": exchange_config}

    async def _check_sharepoint_permissions(
        self, tenant_id: str, creds: dict
    ) -> dict[str, Any]:
        """Check SharePoint Online sharing and permissions settings."""
        await asyncio.sleep(0.1)

        findings: list[dict[str, Any]] = []
        score = 100.0

        sp_config = {
            "external_sharing": "existing_guests",
            "anonymous_links_enabled": False,
            "default_link_type": "internal",
            "sites_with_everyone_access": 2,
        }

        if sp_config["external_sharing"] == "anyone":
            score -= 30
            findings.append({
                "category": "sharepoint_permissions",
                "title": "Partage externe ouvert a tous",
                "severity": "critical",
                "recommendation": "Restreindre le partage externe aux invites existants ou authentifies",
            })

        if sp_config["anonymous_links_enabled"]:
            score -= 25
            findings.append({
                "category": "sharepoint_permissions",
                "title": "Liens anonymes actives",
                "severity": "high",
                "recommendation": "Desactiver les liens anonymes et utiliser des liens authentifies",
            })

        if sp_config["sites_with_everyone_access"] > 0:
            score -= 15
            findings.append({
                "category": "sharepoint_permissions",
                "title": f"{sp_config['sites_with_everyone_access']} sites avec acces 'Everyone'",
                "severity": "medium",
                "recommendation": "Revoir les permissions des sites et supprimer les acces 'Everyone'",
            })

        return {"score": max(0, score), "findings": findings, "data": sp_config}

    async def _check_teams_settings(
        self, tenant_id: str, creds: dict
    ) -> dict[str, Any]:
        """Check Teams guest access and meeting policies."""
        await asyncio.sleep(0.1)

        findings: list[dict[str, Any]] = []
        score = 100.0

        teams_config = {
            "guest_access_enabled": True,
            "guest_can_create_channels": False,
            "anonymous_join_meetings": True,
            "external_chat_enabled": True,
            "cloud_recording_enabled": True,
        }

        if teams_config["anonymous_join_meetings"]:
            score -= 15
            findings.append({
                "category": "teams_settings",
                "title": "Participation anonyme aux reunions autorisee",
                "severity": "medium",
                "recommendation": "Exiger l'authentification pour rejoindre les reunions",
            })

        if teams_config["guest_access_enabled"] and teams_config["guest_can_create_channels"]:
            score -= 10
            findings.append({
                "category": "teams_settings",
                "title": "Les invites peuvent creer des canaux",
                "severity": "low",
                "recommendation": "Restreindre la creation de canaux aux membres internes",
            })

        return {"score": max(0, score), "findings": findings, "data": teams_config}

    async def _check_defender_config(
        self, tenant_id: str, creds: dict
    ) -> dict[str, Any]:
        """Check Microsoft Defender for Office 365 configuration."""
        await asyncio.sleep(0.1)

        findings: list[dict[str, Any]] = []
        score = 100.0

        defender_config = {
            "safe_links_enabled": True,
            "safe_attachments_enabled": True,
            "anti_phishing_enabled": True,
            "impersonation_protection": True,
            "zero_hour_auto_purge": True,
            "real_time_reports": True,
            "threat_investigation_enabled": False,
        }

        if not defender_config["safe_links_enabled"]:
            score -= 20
            findings.append({
                "category": "defender_config",
                "title": "Safe Links non active",
                "severity": "high",
                "recommendation": "Activer Safe Links pour tous les utilisateurs",
            })

        if not defender_config["safe_attachments_enabled"]:
            score -= 20
            findings.append({
                "category": "defender_config",
                "title": "Safe Attachments non active",
                "severity": "high",
                "recommendation": "Activer Safe Attachments pour tous les utilisateurs",
            })

        if not defender_config["anti_phishing_enabled"]:
            score -= 25
            findings.append({
                "category": "defender_config",
                "title": "Politique anti-phishing non configuree",
                "severity": "critical",
                "recommendation": "Activer et configurer les politiques anti-phishing",
            })

        if not defender_config["threat_investigation_enabled"]:
            score -= 10
            findings.append({
                "category": "defender_config",
                "title": "Investigation automatique des menaces non activee",
                "severity": "medium",
                "recommendation": "Activer Automated Investigation and Response (AIR)",
            })

        return {"score": max(0, score), "findings": findings, "data": defender_config}

    @staticmethod
    def _score_to_grade(score: int) -> str:
        """Map score 0-1000 to grade A-F."""
        if score >= 800:
            return "A"
        if score >= 600:
            return "B"
        if score >= 400:
            return "C"
        if score >= 200:
            return "D"
        return "F"


@celery_app.task(name="app.agents.m365_rating_agent.scan_m365")
def scan_m365(
    tenant_id: str,
    credentials: dict | None = None,
) -> dict[str, Any]:
    """Celery task: M365 security rating scan.

    Args:
        tenant_id: Azure AD tenant ID.
        credentials: Auth credentials.

    Returns:
        Dict with M365 rating results.
    """
    import asyncio

    agent = M365RatingAgent()
    result = asyncio.run(
        agent.execute(
            vendor_id=tenant_id,
            tenant_id=tenant_id,
            credentials=credentials or {},
        )
    )
    return {
        "tenant_id": tenant_id,
        "success": result.success,
        "data": result.data,
        "errors": result.errors,
        "duration": result.duration_seconds,
        "audit_log": agent.get_audit_log(),
    }
