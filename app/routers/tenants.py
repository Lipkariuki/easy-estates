from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..dependencies import get_current_user, require_roles
from ..models import Tenant, TenantDocument
from ..schemas import (
    TenantCreate,
    TenantListResponse,
    TenantOut,
    TenantQuery,
    TenantUpdate,
)

router = APIRouter(prefix="/tenants", tags=["Tenants"])


def _tenant_to_schema(tenant: Tenant, pending_documents: int = 0) -> TenantOut:
    return TenantOut(
        id=tenant.id,
        full_name=tenant.full_name,
        email=tenant.email,
        phone=tenant.phone,
        id_number=tenant.id_number,
        kyc_status=tenant.kyc_status,
        kyc_score=tenant.kyc_score,
        kyc_override=tenant.kyc_override,
        pending_documents=pending_documents,
        created_at=tenant.created_at,
    )


@router.get("/", response_model=TenantListResponse)
def list_tenants(
    query: TenantQuery = Depends(),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    stmt = db.query(Tenant)

    if query.status:
        stmt = stmt.filter(Tenant.kyc_status == query.status)

    if query.search:
        like = f"%{query.search.lower()}%"
        stmt = stmt.filter(
            func.lower(Tenant.full_name).like(like)
            | func.lower(Tenant.phone).like(like)
            | func.lower(func.coalesce(Tenant.email, "")).like(like)
        )

    total = stmt.count()
    tenants = (
        stmt.order_by(Tenant.created_at.desc())
        .offset(query.offset)
        .limit(query.limit)
        .all()
    )

    pending_docs_map = {}
    if tenants:
        tenant_ids = [t.id for t in tenants]
        pending_docs_map = dict(
            db.query(TenantDocument.tenant_id, func.count(TenantDocument.id))
            .filter(
                TenantDocument.tenant_id.in_(tenant_ids),
                TenantDocument.status == "pending",
            )
            .group_by(TenantDocument.tenant_id)
            .all()
        )

    items = [
        _tenant_to_schema(tenant, pending_docs_map.get(tenant.id, 0))
        for tenant in tenants
    ]

    return TenantListResponse(items=items, total=total)


@router.post("/", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager")),
):
    tenant = Tenant(**payload.dict())
    # Default new tenants to pending status
    if not tenant.kyc_status:
        tenant.kyc_status = "pending"
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return _tenant_to_schema(tenant, pending_documents=0)


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    pending_docs = (
        db.query(func.count(TenantDocument.id))
        .filter(TenantDocument.tenant_id == tenant_id, TenantDocument.status == "pending")
        .scalar()
    ) or 0

    return _tenant_to_schema(tenant, pending_docs)


@router.patch("/{tenant_id}", response_model=TenantOut)
def update_tenant(
    tenant_id: int,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager")),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(tenant, key, value)

    db.commit()
    db.refresh(tenant)

    pending_docs = (
        db.query(func.count(TenantDocument.id))
        .filter(TenantDocument.tenant_id == tenant_id, TenantDocument.status == "pending")
        .scalar()
    ) or 0

    return _tenant_to_schema(tenant, pending_docs)
