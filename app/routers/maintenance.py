from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..dependencies import get_current_user, require_roles
from ..models import MaintenanceRequest, Property, Tenant, Unit
from ..schemas import (
    MaintenanceCreate,
    MaintenanceListResponse,
    MaintenanceOut,
    MaintenanceUpdate,
)

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


def _to_schema(record: MaintenanceRequest, property_name: str | None, unit_name: str | None, tenant_name: str | None) -> MaintenanceOut:
    return MaintenanceOut(
        id=record.id,
        property_id=record.property_id,
        property_name=property_name,
        unit_id=record.unit_id,
        unit_name=unit_name,
        tenant_id=record.tenant_id,
        tenant_name=tenant_name,
        title=record.title,
        description=record.description,
        priority=record.priority,
        status=record.status,
        reported_on=record.reported_on,
        resolved_on=record.resolved_on,
        assigned_to_id=record.assigned_to_id,
        created_at=record.created_at,
    )


@router.get("/", response_model=MaintenanceListResponse)
def list_requests(db: Session = Depends(get_db), user=Depends(get_current_user)):
    records = (
        db.query(MaintenanceRequest)
        .order_by(MaintenanceRequest.created_at.desc())
        .limit(100)
        .all()
    )

    property_map = {p.id: p for p in db.query(Property).filter(Property.id.in_([r.property_id for r in records])).all()}
    unit_ids = [r.unit_id for r in records if r.unit_id]
    unit_map = {u.id: u for u in db.query(Unit).filter(Unit.id.in_(unit_ids)).all()} if unit_ids else {}
    tenant_ids = [r.tenant_id for r in records if r.tenant_id]
    tenant_map = {t.id: t for t in db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).all()} if tenant_ids else {}

    items = [
        _to_schema(
            record,
            property_map.get(record.property_id).name if property_map.get(record.property_id) else None,
            unit_map.get(record.unit_id).name if unit_map.get(record.unit_id) else None,
            tenant_map.get(record.tenant_id).full_name if tenant_map.get(record.tenant_id) else None,
        )
        for record in records
    ]

    return MaintenanceListResponse(items=items, total=len(items))


@router.post("/", response_model=MaintenanceOut, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: MaintenanceCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager", "caretaker")),
):
    property_obj = db.query(Property).filter(Property.id == payload.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    record = MaintenanceRequest(**payload.dict())
    db.add(record)
    db.commit()
    db.refresh(record)

    unit = db.query(Unit).filter(Unit.id == record.unit_id).first() if record.unit_id else None
    tenant = db.query(Tenant).filter(Tenant.id == record.tenant_id).first() if record.tenant_id else None

    return _to_schema(record, property_obj.name, unit.name if unit else None, tenant.full_name if tenant else None)


@router.patch("/{request_id}", response_model=MaintenanceOut)
def update_request(
    request_id: int,
    payload: MaintenanceUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager", "caretaker")),
):
    record = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)

    property_obj = db.query(Property).filter(Property.id == record.property_id).first()
    unit = db.query(Unit).filter(Unit.id == record.unit_id).first() if record.unit_id else None
    tenant = db.query(Tenant).filter(Tenant.id == record.tenant_id).first() if record.tenant_id else None

    return _to_schema(
        record,
        property_obj.name if property_obj else None,
        unit.name if unit else None,
        tenant.full_name if tenant else None,
    )
