from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .shared import PaginationQuery


class TenantCreate(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    id_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: Optional[str] = None


class TenantUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    id_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: Optional[str] = None
    kyc_status: Optional[str] = Field(default=None, pattern=r"^(pending|submitted|approved|conditional|declined)$")
    kyc_override: Optional[bool] = None
    kyc_notes: Optional[str] = None


class TenantOut(BaseModel):
    id: int
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    id_number: Optional[str]
    kyc_status: str
    kyc_score: int
    kyc_override: bool
    pending_documents: int
    created_at: datetime


class TenantListResponse(BaseModel):
    items: list[TenantOut]
    total: int


class TenantQuery(PaginationQuery):
    status: Optional[str] = Field(default=None, pattern=r"^(pending|submitted|approved|conditional|declined)$")
    search: Optional[str] = None
    property_id: Optional[int] = None
