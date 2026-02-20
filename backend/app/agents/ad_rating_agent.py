"""AD Rating Agent — scans Active Directory for security misconfigurations.

Checks privileged accounts, GPO security, Kerberoasting risk,
delegation misconfigs, dormant accounts, and password policies.
Produces a score 0-1000 with detailed findings.
"""

import asyncio
import logging
import time
from typing import Any
from uuid import uuid4

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.celery_app import celery_app

logger = logging.getLogger("mh_cyberscore.agents.ad_rating")

# Scoring weights per check category
AD_WEIGHTS = {
    "privileged_accounts": 0.20,
    "gpo_security": 0.15,
    "kerberoasting": 0.15,
    "delegations": 0.15,
    "dormant_accounts": 0.15,
    "password_policy": 0.20,
}

# Thresholds for scoring deductions
ADMIN_COUNT_THRESHOLDS = {"good": 5, "warning": 15, "critical": 30}
DORMANT_THRESHOLD_DAYS = 90


class ADRatingAgent(BaseAgent):
    """Active Directory security rating agent."""

    def __init__(self) -> None:
        super().__init__(name="ad_rating", timeout=60.0, rate_limit_per_sec=2.0)

    async def execute(self, vendor_id: str, **kwargs: Any) -> AgentResult:
        """Execute AD security assessment.

        Args:
            vendor_id: Unused for internal scans; pass target identifier.
            **kwargs: Must contain 'domain_controller' and 'credentials'.

        Returns:
            AgentResult with AD security data and score.
        """
        domain_controller = kwargs.get("domain_controller", "")
        credentials = kwargs.get("credentials", {})
        threshold = kwargs.get("threshold_dormant_days", DORMANT_THRESHOLD_DAYS)
        start = time.monotonic()
        errors: list[str] = []
        findings: list[dict[str, Any]] = []
        category_scores: dict[str, float] = {}

        self.logger.info("Starting AD rating scan for %s", domain_controller)

        # Check 1: Privileged accounts
        try:
            result = await self._check_privileged_accounts(
                domain_controller, credentials
            )
            category_scores["privileged_accounts"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"Privileged accounts check: {exc}")
            category_scores["privileged_accounts"] = 50.0

        # Check 2: GPO security
        try:
            result = await self._check_gpo_security(domain_controller, credentials)
            category_scores["gpo_security"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"GPO security check: {exc}")
            category_scores["gpo_security"] = 50.0

        # Check 3: Kerberoasting risk
        try:
            result = await self._check_kerberoasting(domain_controller, credentials)
            category_scores["kerberoasting"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"Kerberoasting check: {exc}")
            category_scores["kerberoasting"] = 50.0

        # Check 4: Delegation misconfigs
        try:
            result = await self._check_delegations(domain_controller, credentials)
            category_scores["delegations"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"Delegation check: {exc}")
            category_scores["delegations"] = 50.0

        # Check 5: Dormant accounts
        try:
            result = await self._check_dormant_accounts(
                domain_controller, credentials, threshold
            )
            category_scores["dormant_accounts"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"Dormant accounts check: {exc}")
            category_scores["dormant_accounts"] = 50.0

        # Check 6: Password policy
        try:
            result = await self._check_password_policy(
                domain_controller, credentials
            )
            category_scores["password_policy"] = result["score"]
            findings.extend(result["findings"])
        except Exception as exc:
            errors.append(f"Password policy check: {exc}")
            category_scores["password_policy"] = 50.0

        # Calculate weighted global score
        global_score = 0.0
        for category, weight in AD_WEIGHTS.items():
            global_score += category_scores.get(category, 50.0) * weight
        global_score = int(max(0, min(1000, global_score * 10)))

        grade = self._score_to_grade(global_score)

        duration = time.monotonic() - start
        return AgentResult(
            agent_name=self.name,
            vendor_id=vendor_id,
            success=len(errors) < 3,
            data={
                "domain_controller": domain_controller,
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

    async def _check_privileged_accounts(
        self, dc: str, creds: dict
    ) -> dict[str, Any]:
        """Count admin accounts, service accounts, nested group memberships.

        In production, this queries LDAP. Here we simulate the check structure.
        """
        await asyncio.sleep(0.1)  # Simulate LDAP query

        # Simulated analysis — in production, query AD via ldap3
        admin_count = 0
        service_accounts = 0
        nested_groups = 0
        findings: list[dict[str, Any]] = []
        score = 100.0

        # This would normally query:
        # - Domain Admins, Enterprise Admins, Schema Admins membership
        # - Service accounts with admin privileges
        # - Nested group depth analysis
        admin_count = 8  # Placeholder for LDAP result
        service_accounts = 3
        nested_groups = 2

        if admin_count > ADMIN_COUNT_THRESHOLDS["critical"]:
            score -= 40
            findings.append({
                "category": "privileged_accounts",
                "title": f"Nombre excessif de comptes admin: {admin_count}",
                "description": f"{admin_count} comptes avec privileges administrateur detectes",
                "severity": "critical",
                "recommendation": "Reduire le nombre de comptes admin a moins de 5",
            })
        elif admin_count > ADMIN_COUNT_THRESHOLDS["warning"]:
            score -= 20
            findings.append({
                "category": "privileged_accounts",
                "title": f"Nombre eleve de comptes admin: {admin_count}",
                "description": f"{admin_count} comptes avec privileges administrateur",
                "severity": "high",
                "recommendation": "Auditer et reduire les comptes admin",
            })
        elif admin_count > ADMIN_COUNT_THRESHOLDS["good"]:
            score -= 10
            findings.append({
                "category": "privileged_accounts",
                "title": f"{admin_count} comptes admin detectes",
                "description": "Nombre acceptable mais a surveiller",
                "severity": "medium",
                "recommendation": "Maintenir une revue reguliere des comptes admin",
            })

        if service_accounts > 5:
            score -= 15
            findings.append({
                "category": "privileged_accounts",
                "title": f"{service_accounts} comptes de service avec privileges eleves",
                "severity": "high",
                "recommendation": "Utiliser des gMSA pour les comptes de service",
            })

        return {
            "score": max(0, score),
            "findings": findings,
            "data": {
                "admin_count": admin_count,
                "service_accounts": service_accounts,
                "nested_groups": nested_groups,
            },
        }

    async def _check_gpo_security(
        self, dc: str, creds: dict
    ) -> dict[str, Any]:
        """Analyze Group Policy Objects for security misconfigurations."""
        await asyncio.sleep(0.1)

        findings: list[dict[str, Any]] = []
        score = 100.0

        # Simulated GPO checks — in production, query SYSVOL/LDAP
        checks = {
            "password_never_expires_gpo": False,
            "laps_deployed": True,
            "audit_policy_configured": True,
            "smb_signing_required": True,
            "ntlm_restricted": False,
        }

        if not checks["ntlm_restricted"]:
            score -= 25
            findings.append({
                "category": "gpo_security",
                "title": "NTLM non restreint par GPO",
                "description": "L'authentification NTLM n'est pas restreinte, risque de relay attacks",
                "severity": "high",
                "recommendation": "Configurer une GPO pour restreindre NTLM et privileger Kerberos",
            })

        if checks["password_never_expires_gpo"]:
            score -= 20
            findings.append({
                "category": "gpo_security",
                "title": "GPO autorisant les mots de passe sans expiration",
                "severity": "high",
                "recommendation": "Supprimer la GPO ou modifier la politique d'expiration",
            })

        if not checks["laps_deployed"]:
            score -= 20
            findings.append({
                "category": "gpo_security",
                "title": "LAPS non deploye",
                "description": "Local Administrator Password Solution non configure",
                "severity": "high",
                "recommendation": "Deployer LAPS via GPO sur tous les postes",
            })

        return {"score": max(0, score), "findings": findings}

    async def _check_kerberoasting(
        self, dc: str, creds: dict
    ) -> dict[str, Any]:
        """Check for SPNs on user accounts (Kerberoasting risk)."""
        await asyncio.sleep(0.1)

        findings: list[dict[str, Any]] = []
        score = 100.0

        # Simulated — in production, LDAP query for servicePrincipalName on user objects
        spn_users = 2  # Number of user accounts with SPNs

        if spn_users > 0:
            severity = "critical" if spn_users > 5 else "high" if spn_users > 2 else "medium"
            deduction = min(50, spn_users * 10)
            score -= deduction
            findings.append({
                "category": "kerberoasting",
                "title": f"{spn_users} comptes utilisateur avec SPN (Kerberoasting)",
                "description": "Des comptes utilisateur ont des SPNs, vulnerables au Kerberoasting",
                "severity": severity,
                "recommendation": "Migrer les SPNs vers des comptes gMSA ou supprimer les SPNs inutiles",
            })

        return {"score": max(0, score), "findings": findings}

    async def _check_delegations(
        self, dc: str, creds: dict
    ) -> dict[str, Any]:
        """Check for unconstrained and constrained delegation misconfigs."""
        await asyncio.sleep(0.1)

        findings: list[dict[str, Any]] = []
        score = 100.0

        # Simulated — in production, check TRUSTED_FOR_DELEGATION flag
        unconstrained = 1
        constrained_any_protocol = 0

        if unconstrained > 0:
            score -= 30
            findings.append({
                "category": "delegations",
                "title": f"{unconstrained} objet(s) avec delegation sans contrainte",
                "description": "La delegation sans contrainte permet l'usurpation de tout utilisateur",
                "severity": "critical",
                "recommendation": "Migrer vers la delegation contrainte basee sur les ressources",
            })

        if constrained_any_protocol > 0:
            score -= 15
            findings.append({
                "category": "delegations",
                "title": f"{constrained_any_protocol} delegation(s) avec 'any protocol'",
                "severity": "high",
                "recommendation": "Restreindre a Kerberos only quand possible",
            })

        return {"score": max(0, score), "findings": findings}

    async def _check_dormant_accounts(
        self, dc: str, creds: dict, threshold: int = 90
    ) -> dict[str, Any]:
        """Find accounts with last login older than threshold days."""
        await asyncio.sleep(0.1)

        findings: list[dict[str, Any]] = []
        score = 100.0

        # Simulated — in production, query lastLogonTimestamp
        dormant_count = 15
        never_logged_in = 3

        if dormant_count > 50:
            score -= 40
            severity = "critical"
        elif dormant_count > 20:
            score -= 25
            severity = "high"
        elif dormant_count > 5:
            score -= 15
            severity = "medium"
        else:
            severity = "low"

        if dormant_count > 0:
            findings.append({
                "category": "dormant_accounts",
                "title": f"{dormant_count} comptes dormants (>{threshold} jours)",
                "description": f"{dormant_count} comptes sans connexion depuis plus de {threshold} jours",
                "severity": severity,
                "recommendation": "Desactiver ou supprimer les comptes dormants",
            })

        if never_logged_in > 0:
            score -= 10
            findings.append({
                "category": "dormant_accounts",
                "title": f"{never_logged_in} comptes jamais utilises",
                "severity": "medium",
                "recommendation": "Verifier et supprimer les comptes jamais utilises",
            })

        return {"score": max(0, score), "findings": findings}

    async def _check_password_policy(
        self, dc: str, creds: dict
    ) -> dict[str, Any]:
        """Evaluate domain password policy (length, complexity, age)."""
        await asyncio.sleep(0.1)

        findings: list[dict[str, Any]] = []
        score = 100.0

        # Simulated — in production, query Default Domain Policy
        policy = {
            "min_length": 8,
            "complexity_enabled": True,
            "max_age_days": 90,
            "min_age_days": 1,
            "history_count": 12,
            "lockout_threshold": 5,
            "lockout_duration_min": 30,
        }

        if policy["min_length"] < 12:
            deduction = 20 if policy["min_length"] < 8 else 10
            score -= deduction
            findings.append({
                "category": "password_policy",
                "title": f"Longueur minimale insuffisante: {policy['min_length']} caracteres",
                "severity": "high" if policy["min_length"] < 8 else "medium",
                "recommendation": "Augmenter la longueur minimale a 12 caracteres ou plus",
            })

        if not policy["complexity_enabled"]:
            score -= 15
            findings.append({
                "category": "password_policy",
                "title": "Complexite de mot de passe non activee",
                "severity": "high",
                "recommendation": "Activer la complexite de mot de passe dans la GPO",
            })

        if policy["max_age_days"] > 180:
            score -= 10
            findings.append({
                "category": "password_policy",
                "title": f"Duree de vie max trop longue: {policy['max_age_days']} jours",
                "severity": "medium",
                "recommendation": "Reduire la duree de vie maximale a 90 jours",
            })

        if policy["lockout_threshold"] == 0:
            score -= 20
            findings.append({
                "category": "password_policy",
                "title": "Pas de verrouillage de compte configure",
                "severity": "critical",
                "recommendation": "Configurer un seuil de verrouillage (5 tentatives recommande)",
            })

        return {
            "score": max(0, score),
            "findings": findings,
            "data": policy,
        }

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


@celery_app.task(name="app.agents.ad_rating_agent.scan_ad")
def scan_ad(
    domain_controller: str,
    credentials: dict | None = None,
    threshold_dormant_days: int = 90,
) -> dict[str, Any]:
    """Celery task: AD security rating scan.

    Args:
        domain_controller: DC hostname or IP.
        credentials: Auth credentials.
        threshold_dormant_days: Dormant account threshold.

    Returns:
        Dict with AD rating results.
    """
    import asyncio

    agent = ADRatingAgent()
    result = asyncio.run(
        agent.execute(
            vendor_id=domain_controller,
            domain_controller=domain_controller,
            credentials=credentials or {},
            threshold_dormant_days=threshold_dormant_days,
        )
    )
    return {
        "domain_controller": domain_controller,
        "success": result.success,
        "data": result.data,
        "errors": result.errors,
        "duration": result.duration_seconds,
        "audit_log": agent.get_audit_log(),
    }
