"""Vendor self-service portal API — scorecard, findings, disputes, questionnaires."""

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.schemas.portal import (
    EvidenceUpload,
    PortalDispute,
    PortalDisputeCreate,
    PortalFinding,
    PortalQuestionnaire,
    PortalScorecard,
    QuestionnaireResponse,
)

router = APIRouter(prefix="/portal", tags=["portal"])

# In-memory stores (replaced by DB in production)
_disputes: dict[str, PortalDispute] = {}
_questionnaire_responses: dict[str, dict[str, str]] = {}


@router.get("/scorecard", response_model=PortalScorecard)
async def get_scorecard() -> PortalScorecard:
    """Return the authenticated vendor's current scorecard.

    In production, the vendor_id comes from the JWT token.
    """
    return PortalScorecard(
        vendor_id="portal-vendor-demo",
        vendor_name="Demo Vendor",
        domain="demo-vendor.com",
        score=720,
        grade="B",
        domain_scores={
            "network_security": 75,
            "dns_security": 80,
            "web_security": 65,
            "email_security": 70,
            "patching_cadence": 60,
            "ip_reputation": 85,
            "leaks_exposure": 70,
            "regulatory_presence": 90,
        },
        last_scan=datetime.now(timezone.utc),
    )


@router.get("/findings", response_model=list[PortalFinding])
async def get_findings() -> list[PortalFinding]:
    """Return findings visible to the authenticated vendor."""
    return [
        PortalFinding(
            id="f-001",
            title="TLS 1.0 still enabled",
            severity="high",
            domain="web_security",
            status="open",
            description="The server still accepts TLS 1.0 connections.",
            detected_at=datetime.now(timezone.utc),
        ),
        PortalFinding(
            id="f-002",
            title="Missing SPF record",
            severity="medium",
            domain="email_security",
            status="open",
            description="No SPF DNS record found for the primary domain.",
            detected_at=datetime.now(timezone.utc),
        ),
        PortalFinding(
            id="f-003",
            title="Open port 3389 (RDP)",
            severity="critical",
            domain="network_security",
            status="open",
            description="RDP port exposed to the internet.",
            detected_at=datetime.now(timezone.utc),
        ),
    ]


@router.post("/disputes", response_model=PortalDispute)
async def create_dispute(body: PortalDisputeCreate) -> PortalDispute:
    """Submit a dispute for a finding."""
    dispute_id = str(uuid.uuid4())
    dispute = PortalDispute(
        id=dispute_id,
        finding_id=body.finding_id,
        reason=body.reason,
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    _disputes[dispute_id] = dispute
    return dispute


@router.post("/disputes/{dispute_id}/evidence", response_model=EvidenceUpload)
async def upload_evidence(
    dispute_id: str,
    file: UploadFile = File(...),
) -> EvidenceUpload:
    """Upload evidence file for a dispute. Stores to MinIO in production."""
    if dispute_id not in _disputes:
        raise HTTPException(status_code=404, detail="Dispute not found")

    content = await file.read()
    size_bytes = len(content)

    # In production, upload to MinIO here
    object_key = f"disputes/{dispute_id}/{file.filename}"
    url = f"/storage/{object_key}"

    _disputes[dispute_id].evidence_urls.append(url)

    return EvidenceUpload(
        dispute_id=dispute_id,
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        url=url,
    )


@router.get("/questionnaires", response_model=list[PortalQuestionnaire])
async def list_questionnaires() -> list[PortalQuestionnaire]:
    """List questionnaires assigned to the vendor."""
    return [
        PortalQuestionnaire(
            id="q-001",
            title="Questionnaire Securite Annuel 2026",
            status="pending",
            due_date=datetime(2026, 6, 30, tzinfo=timezone.utc),
            question_count=25,
        ),
        PortalQuestionnaire(
            id="q-002",
            title="Evaluation DORA — Prestataire TIC",
            status="pending",
            due_date=datetime(2026, 3, 31, tzinfo=timezone.utc),
            question_count=40,
        ),
    ]


@router.post("/questionnaires/{questionnaire_id}/respond")
async def respond_to_questionnaire(
    questionnaire_id: str,
    body: QuestionnaireResponse,
) -> dict[str, Any]:
    """Submit responses to a questionnaire."""
    _questionnaire_responses[questionnaire_id] = body.answers
    return {
        "questionnaire_id": questionnaire_id,
        "status": "submitted",
        "answers_count": len(body.answers),
    }
