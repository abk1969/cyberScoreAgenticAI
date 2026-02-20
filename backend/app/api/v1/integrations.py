"""Integration management API — configure, list, and test integrations."""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas.integration import (
    IntegrationConfig,
    IntegrationListResponse,
    IntegrationStatus,
    IntegrationTestResult,
    IntegrationType,
)
from app.services.integrations import (
    ServiceNowService,
    SlackService,
    SplunkService,
    TeamsService,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _get_status(itype: IntegrationType) -> IntegrationStatus:
    """Build current status for an integration type based on settings."""
    if itype == IntegrationType.splunk:
        svc = SplunkService()
        return IntegrationStatus(
            type=itype,
            enabled=svc.configured,
            configured=svc.configured,
        )
    if itype == IntegrationType.servicenow:
        svc = ServiceNowService()
        return IntegrationStatus(
            type=itype,
            enabled=svc.configured,
            configured=svc.configured,
        )
    if itype == IntegrationType.slack:
        svc = SlackService()
        return IntegrationStatus(
            type=itype,
            enabled=svc.configured,
            configured=svc.configured,
        )
    if itype == IntegrationType.teams:
        svc = TeamsService()
        return IntegrationStatus(
            type=itype,
            enabled=svc.configured,
            configured=svc.configured,
        )
    raise HTTPException(status_code=400, detail=f"Unknown integration type: {itype}")


@router.get("/", response_model=IntegrationListResponse)
async def list_integrations() -> IntegrationListResponse:
    """List all configured integrations and their status."""
    statuses = [_get_status(t) for t in IntegrationType]
    return IntegrationListResponse(integrations=statuses)


@router.put("/{integration_type}", response_model=IntegrationStatus)
async def configure_integration(
    integration_type: IntegrationType,
    config: IntegrationConfig,
) -> IntegrationStatus:
    """Update integration configuration.

    In production this would persist to the database. For now it updates
    the runtime settings object.
    """
    if integration_type == IntegrationType.splunk:
        settings.splunk_hec_url = config.url
        settings.splunk_hec_token = config.token
    elif integration_type == IntegrationType.servicenow:
        settings.servicenow_instance = config.url
        settings.servicenow_user = config.username
        settings.servicenow_password = config.password
    elif integration_type == IntegrationType.slack:
        settings.slack_webhook_url = config.url
    elif integration_type == IntegrationType.teams:
        settings.teams_webhook_url = config.url

    return _get_status(integration_type)


@router.post("/{integration_type}/test", response_model=IntegrationTestResult)
async def test_integration(
    integration_type: IntegrationType,
) -> IntegrationTestResult:
    """Test connectivity for an integration."""
    if integration_type == IntegrationType.splunk:
        result = await SplunkService().test_connection()
    elif integration_type == IntegrationType.servicenow:
        result = await ServiceNowService().test_connection()
    elif integration_type == IntegrationType.slack:
        result = await SlackService().test_connection()
    elif integration_type == IntegrationType.teams:
        result = await TeamsService().test_connection()
    else:
        raise HTTPException(status_code=400, detail="Unknown integration type")

    return IntegrationTestResult(
        type=integration_type,
        success=result["success"],
        message=result["message"],
    )
