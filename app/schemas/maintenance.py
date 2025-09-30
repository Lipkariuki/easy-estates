from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class MaintenanceCreate(BaseModel):
    property_id: int
    unit_id: Optional[int] = None
    tenant_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: Optional[str] = None
    reported_on: date
    assigned_to_id: Optional[int] = None
    notes: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    status: Optional[str] = None
    resolved_on: Optional[date] = None
    assigned_to_id: Optional[int] = None
    notes: Optional[str] = None


class MaintenanceOut(BaseModel):
    id: int
    property_id: int
    property_name: Optional[str]
    unit_id: Optional[int]
    unit_name: Optional[str]
    tenant_id: Optional[int]
    tenant_name: Optional[str]
    title: str
    description: Optional[str]
    priority: str
    status: str
    reported_on: date
    resolved_on: Optional[date]
    assigned_to_id: Optional[int]
    created_at: datetime


class MaintenanceListResponse(BaseModel):
    items: list[MaintenanceOut]
    total: int
