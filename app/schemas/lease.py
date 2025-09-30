from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class LeaseCreate(BaseModel):
    unit_id: int
    tenant_id: int
    start_date: date
    end_date: Optional[date] = None
    rent_amount: float
    deposit_amount: Optional[float] = None
    payment_day: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class LeaseUpdate(BaseModel):
    end_date: Optional[date] = None
    rent_amount: Optional[float] = None
    deposit_amount: Optional[float] = None
    payment_day: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class LeaseOut(BaseModel):
    id: int
    unit_id: int
    tenant_id: int
    start_date: date
    end_date: Optional[date]
    rent_amount: float
    deposit_amount: Optional[float]
    payment_day: Optional[int]
    status: str
    notes: Optional[str]
    created_at: datetime
    tenant_name: Optional[str]
    unit_name: Optional[str]


class RentInvoiceCreate(BaseModel):
    lease_id: int
    period_start: date
    period_end: date
    due_date: date
    amount_due: float
    notes: Optional[str] = None


class RentInvoiceOut(BaseModel):
    id: int
    lease_id: int
    period_start: date
    period_end: date
    due_date: date
    amount_due: float
    amount_paid: float
    status: str
    notes: Optional[str]


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float
    paid_on: date
    method: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentOut(BaseModel):
    id: int
    invoice_id: int
    amount: float
    paid_on: date
    method: str
    reference: Optional[str]
    notes: Optional[str]
    created_at: datetime
