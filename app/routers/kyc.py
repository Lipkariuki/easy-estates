import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..dependencies import require_roles
from ..models import (
    Tenant,
    TenantDocument,
    TenantInvite,
    TenantKycAudit,
    TenantKycSession,
)
from ..schemas import (
    TenantDocumentUpload,
    TenantInviteCreate,
    TenantInviteResponse,
    TenantKycDecision,
    TenantKycSessionCreate,
    TenantKycSessionResponse,
)

router = APIRouter(prefix="/kyc", tags=["Tenant KYC"])


def _build_kyc_url(token: str) -> str:
    return f"{settings.frontend_base_url.rstrip('/')}/kyc/{token}"


@router.post("/invite", response_model=TenantInviteResponse, status_code=status.HTTP_201_CREATED)
def create_invite(
    payload: TenantInviteCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager")),
):
    tenant = db.query(Tenant).filter(Tenant.id == payload.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours)

    invite = TenantInvite(
        tenant_id=tenant.id,
        email=payload.email,
        token=token,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()

    return TenantInviteResponse(tenant_id=tenant.id, token=token, expires_at=expires_at)


@router.post("/session", response_model=TenantKycSessionResponse, status_code=status.HTTP_201_CREATED)
def create_kyc_session(
    payload: TenantKycSessionCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager", "caretaker")),
):
    tenant = db.query(Tenant).filter(Tenant.id == payload.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours)

    session = TenantKycSession(
        tenant_id=tenant.id,
        token=token,
        expires_at=expires_at,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return TenantKycSessionResponse(
        id=session.id,
        tenant_id=session.tenant_id,
        token=session.token,
        status=session.status,
        expires_at=session.expires_at,
        verify_url=_build_kyc_url(session.token),
    )


@router.post("/documents", status_code=status.HTTP_201_CREATED)
def upload_document(
    payload: TenantDocumentUpload,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager", "caretaker")),
):
    tenant = db.query(Tenant).filter(Tenant.id == payload.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    document = TenantDocument(
        tenant_id=payload.tenant_id,
        doc_type=payload.doc_type,
        file_url=payload.file_url,
        score_value=payload.score_value,
    )
    db.add(document)

    tenant.kyc_status = tenant.kyc_status or "submitted"
    tenant.kyc_score = (tenant.kyc_score or 0) + payload.score_value

    db.commit()

    return {"message": "Document stored"}


@router.post("/decision", status_code=status.HTTP_200_OK)
def record_decision(
    payload: TenantKycDecision,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager")),
):
    tenant = db.query(Tenant).filter(Tenant.id == payload.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    previous = tenant.kyc_status
    tenant.kyc_status = payload.new_status
    tenant.kyc_reviewed_by_id = user.id
    tenant.kyc_reviewed_at = datetime.now(timezone.utc)

    audit = TenantKycAudit(
        tenant_id=tenant.id,
        previous_status=previous,
        new_status=payload.new_status,
        changed_by_id=user.id,
        reason=payload.reason,
    )
    db.add(audit)
    db.commit()

    return {"message": "KYC decision recorded"}
