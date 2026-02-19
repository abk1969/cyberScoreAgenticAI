# MH-CyberScore Compliance & Security Skill

## Description
Guide for implementing security, compliance (DORA, RGPD, NIS2, AI Act), and sovereignty requirements in MH-CyberScore. Use when building auth systems, RBAC, audit trails, encryption, DORA register, or any compliance-related feature.

## Regulatory Framework

### DORA (Digital Operational Resilience Act)
- **Scope**: Cartography of ICT providers, continuous monitoring, concentration risk, information register, resilience tests
- **Key articles**: 5-16, 17-23, 24-27, **28-30** (third-party risk)
- **Impact**: Native integration in scoring methodology, DORA register for ACPR

### RGPD
- **Legal basis**: Legitimate interest (art. 6.1.f) for supply chain security
- **Minimization**: Collect only public data necessary for scoring
- **Right of opposition**: Documented process for evaluated vendors
- **Retention**: Raw data 90 days, aggregated scores 3 years
- **AIPD**: Impact analysis required before production

### NIS2
- **Scope**: Supply chain security, incident notification
- **Key articles**: 21, 23

### AI Act
- **Classification**: Limited risk AI system (vendor scoring, not HR or credit)
- **Transparency**: Vendors informed they're evaluated by AI
- **Explainability**: SHAP values for each scoring factor
- **Human oversight**: Business decisions (vendor rejection) require human validation

## Authentication & Authorization

### Keycloak Configuration
```
- SSO via Keycloak 24 (OIDC/SAML integrated with AD Malakoff Humanis)
- MFA mandatory for ALL accounts
- Session timeout: 30 min inactivity, 8h max
- API: JWT signed RS256, key rotation every 90 days
```

### RBAC Roles
| Role | Permissions |
|------|------------|
| Admin | Full configuration, user management |
| RSSI | Read/write all modules, dispute validation |
| Analyste SSI | Read/write scoring + VRM |
| Direction Achats | Read portfolios + reports + questionnaires |
| COMEX | Read executive dashboard + reports |
| Fournisseur | Portal access only (own scorecard + dispute) |

### Auth Implementation Pattern
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(token = Depends(security)):
    try:
        payload = jwt.decode(
            token.credentials,
            settings.jwt_public_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.keycloak_client_id,
        )
        return UserClaims(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

def require_role(*roles: str):
    async def role_checker(user = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    return role_checker

# Usage:
@router.get("/admin/users")
async def list_users(user = Depends(require_role("admin", "rssi"))):
    ...
```

## Encryption

### Transport
- TLS 1.3 exclusive (NO TLS 1.2 fallback)

### At Rest
- AES-256-GCM for all database data
- Keys managed via HSM (Thales Luna or sovereign equivalent)

### Secrets Management
- HashiCorp Vault (self-hosted)
- NEVER hardcode secrets in code
- All secrets via environment variables or Vault API

## Audit Trail

### What to Log
- All authenticated access (who, what, when, from where)
- Every score modification with before/after values
- Every dispute action
- Every report generation
- Every agent execution with inputs/outputs
- Every API call to external services

### Log Implementation Pattern
```python
from datetime import datetime
from sqlalchemy import String, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[str] = mapped_column(String(36))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str] = mapped_column(String(45))
    user_agent: Mapped[str] = mapped_column(String(500))
```

### Centralized Logging
- Logs centralized in Loki, retention 1 year minimum
- Automatic SIEM alerts on abnormal behavior
- Complete audit trail for every score modification

## DORA Register

### Required Fields (art. 28)
```python
class DORARegisterEntry(Base):
    __tablename__ = "dora_register"

    id: Mapped[str] = mapped_column(primary_key=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"))
    # Identification
    vendor_name: Mapped[str]
    vendor_type: Mapped[str]  # ICT service type
    contract_reference: Mapped[str]
    # Criticality
    is_critical: Mapped[bool]
    criticality_justification: Mapped[str]
    # Service details
    service_description: Mapped[str]
    data_types_processed: Mapped[list]  # JSON
    data_locations: Mapped[list]  # Countries
    # Subcontracting
    subcontractors: Mapped[list]  # JSON
    subcontracting_chain_mapped: Mapped[bool]
    # Risk assessment
    last_risk_assessment_date: Mapped[datetime]
    risk_score: Mapped[int]
    # Exit strategy
    exit_plan_exists: Mapped[bool]
    exit_plan_last_tested: Mapped[datetime | None]
    # Compliance
    certifications: Mapped[list]  # ISO 27001, HDS, etc.
    last_audit_date: Mapped[datetime | None]
```

## Code Security Pipeline

### SAST (Static Analysis)
- Semgrep in CI pipeline
- Custom rules for sovereignty violations (detect US service imports)

### DAST (Dynamic Analysis)
- OWASP ZAP automated on every staging deployment

### SCA (Software Composition Analysis)
- Trivy for dependencies and Docker images

### Secret Scanning
- gitleaks in pre-commit hooks

### Code Review
- 2 reviewers minimum (1 senior)
- Security checklist for every MR

## Sovereignty Checklist
For EVERY new feature or integration, verify:
- [ ] No data transits through US-controlled servers
- [ ] No direct US API calls without sovereign proxy
- [ ] No US CDN for serving content
- [ ] Encryption keys managed by MH (not cloud provider)
- [ ] Logs stored on French soil only
- [ ] Dependencies from European registries preferred
- [ ] RGPD processing register updated
