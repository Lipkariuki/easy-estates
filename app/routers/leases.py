from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..dependencies import get_current_user, require_roles
from ..models import Lease, Payment, RentInvoice, Tenant, Unit
from ..schemas import (
    LeaseCreate,
    LeaseOut,
    LeaseUpdate,
    PaymentCreate,
    PaymentOut,
    RentInvoiceCreate,
    RentInvoiceOut,
)

router = APIRouter(prefix="/leases", tags=["Leases"])


def _lease_to_schema(lease: Lease, tenant: Tenant | None, unit: Unit | None) -> LeaseOut:
    return LeaseOut(
        id=lease.id,
        unit_id=lease.unit_id,
        tenant_id=lease.tenant_id,
        start_date=lease.start_date,
        end_date=lease.end_date,
        rent_amount=float(lease.rent_amount or 0),
        deposit_amount=float(lease.deposit_amount or 0) if lease.deposit_amount else None,
        payment_day=lease.payment_day,
        status=lease.status,
        notes=lease.notes,
        created_at=lease.created_at,
        tenant_name=tenant.full_name if tenant else None,
        unit_name=unit.name if unit else None,
    )


@router.get("/", response_model=list[LeaseOut])
def list_leases(db: Session = Depends(get_db), user=Depends(get_current_user)):
    leases = db.query(Lease).order_by(Lease.created_at.desc()).limit(100).all()
    tenant_map = {t.id: t for t in db.query(Tenant).filter(Tenant.id.in_([l.tenant_id for l in leases])).all()}
    unit_map = {u.id: u for u in db.query(Unit).filter(Unit.id.in_([l.unit_id for l in leases])).all()}
    return [_lease_to_schema(l, tenant_map.get(l.tenant_id), unit_map.get(l.unit_id)) for l in leases]


@router.post("/", response_model=LeaseOut, status_code=status.HTTP_201_CREATED)
def create_lease(
    payload: LeaseCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager")),
):
    unit = db.query(Unit).filter(Unit.id == payload.unit_id).first()
    tenant = db.query(Tenant).filter(Tenant.id == payload.tenant_id).first()
    if not unit or not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit or tenant missing")

    lease = Lease(**payload.dict())
    lease.status = lease.status or "active"
    db.add(lease)
    db.commit()
    db.refresh(lease)

    return _lease_to_schema(lease, tenant, unit)


@router.get("/{lease_id}", response_model=LeaseOut)
def get_lease(lease_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")

    tenant = db.query(Tenant).filter(Tenant.id == lease.tenant_id).first()
    unit = db.query(Unit).filter(Unit.id == lease.unit_id).first()
    return _lease_to_schema(lease, tenant, unit)


@router.patch("/{lease_id}", response_model=LeaseOut)
def update_lease(
    lease_id: int,
    payload: LeaseUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager")),
):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(lease, key, value)

    db.commit()
    db.refresh(lease)

    tenant = db.query(Tenant).filter(Tenant.id == lease.tenant_id).first()
    unit = db.query(Unit).filter(Unit.id == lease.unit_id).first()
    return _lease_to_schema(lease, tenant, unit)


@router.post("/{lease_id}/invoices", response_model=RentInvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    lease_id: int,
    payload: RentInvoiceCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager")),
):
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lease not found")

    invoice = RentInvoice(**payload.dict())
    invoice.lease_id = lease_id
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return RentInvoiceOut(
        id=invoice.id,
        lease_id=invoice.lease_id,
        period_start=invoice.period_start,
        period_end=invoice.period_end,
        due_date=invoice.due_date,
        amount_due=float(invoice.amount_due or 0),
        amount_paid=float(invoice.amount_paid or 0),
        status=invoice.status,
        notes=invoice.notes,
    )


@router.post("/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager", "caretaker")),
):
    invoice = db.query(RentInvoice).filter(RentInvoice.id == payload.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    payment = Payment(**payload.dict())
    db.add(payment)

    invoice.amount_paid = (invoice.amount_paid or 0) + payload.amount
    if invoice.amount_paid >= invoice.amount_due:
        invoice.status = "paid"
    elif invoice.amount_paid > 0:
        invoice.status = "partial"
    else:
        invoice.status = "pending"

    db.commit()
    db.refresh(payment)

    return PaymentOut(
        id=payment.id,
        invoice_id=payment.invoice_id,
        amount=float(payment.amount),
        paid_on=payment.paid_on,
        method=payment.method,
        reference=payment.reference,
        notes=payment.notes,
        created_at=payment.created_at,
    )
