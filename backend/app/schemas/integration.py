"""Schemas for integration configuration and testing."""

from enum import Enum

from pydantic import BaseModel, Field


class IntegrationType(str, Enum):
    splunk = "splunk"
    servicenow = "servicenow"
    slack = "slack"
    teams = "teams"


class IntegrationConfig(BaseModel):
    """Configuration for an integration."""

    type: IntegrationType
    enabled: bool = False
    url: str = ""
    token: str = ""
    username: str = ""
    password: str = ""
    extra: dict[str, str] = Field(default_factory=dict)


class IntegrationStatus(BaseModel):
    """Current status of a configured integration."""

    type: IntegrationType
    enabled: bool
    configured: bool
    last_test_success: bool | None = None
    last_test_message: str | None = None


class IntegrationTestResult(BaseModel):
    """Result of an integration connectivity test."""

    type: IntegrationType
    success: bool
    message: str


class IntegrationListResponse(BaseModel):
    """List of all integration statuses."""

    integrations: list[IntegrationStatus]
