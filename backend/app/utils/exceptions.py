"""Custom exception hierarchy for CyberScore."""


class CyberScoreError(Exception):
    """Base exception for all CyberScore errors."""

    def __init__(self, message: str = "An internal error occurred", code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class VendorNotFoundError(CyberScoreError):
    """Raised when a vendor cannot be found."""

    def __init__(self, vendor_id: str):
        super().__init__(
            message=f"Vendor not found: {vendor_id}",
            code="VENDOR_NOT_FOUND",
        )


class VendorAlreadyExistsError(CyberScoreError):
    """Raised when creating a vendor with a duplicate domain."""

    def __init__(self, domain: str):
        super().__init__(
            message=f"A vendor with domain '{domain}' already exists",
            code="VENDOR_ALREADY_EXISTS",
        )


class ScoringError(CyberScoreError):
    """Raised when the scoring engine encounters an error."""

    def __init__(self, message: str = "Scoring engine error"):
        super().__init__(message=message, code="SCORING_ERROR")


class AuthenticationError(CyberScoreError):
    """Raised on authentication failures."""

    def __init__(self, message: str = "Invalid authentication credentials"):
        super().__init__(message=message, code="AUTH_ERROR")


class AuthorizationError(CyberScoreError):
    """Raised when a user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, code="FORBIDDEN")


class ReportGenerationError(CyberScoreError):
    """Raised when report generation fails."""

    def __init__(self, message: str = "Report generation failed"):
        super().__init__(message=message, code="REPORT_ERROR")


class ExternalServiceError(CyberScoreError):
    """Raised when an external OSINT API call fails."""

    def __init__(self, service: str, message: str = ""):
        super().__init__(
            message=f"External service '{service}' error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
        )


class ValidationError(CyberScoreError):
    """Raised on business logic validation failures."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, code="VALIDATION_ERROR")


class ToolError(ExternalServiceError):
    """Raised when an OSINT tool API call fails."""

    def __init__(self, message: str = "Tool error"):
        super().__init__(service="tool", message=message)


class AgentError(CyberScoreError):
    """Raised when an agent execution fails."""

    def __init__(self, message: str = "Agent execution error"):
        super().__init__(message=message, code="AGENT_ERROR")
