from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TenantInviteCreate(BaseModel):
    tenant_id: int
    email: str
    expires_in_hours: int = 24


class TenantInviteResponse(BaseModel):
    tenant_id: int
    token: str
    expires_at: datetime


class TenantDocumentUpload(BaseModel):
    tenant_id: int
    doc_type: str
    file_url: str
    score_value: int = 0


class TenantKycSessionCreate(BaseModel):
    tenant_id: int
    expires_in_hours: int = 24


class TenantKycSessionResponse(BaseModel):
    id: int
    tenant_id: int
    token: str
    status: str
    expires_at: datetime
    verify_url: str


class TenantKycDecision(BaseModel):
    tenant_id: int
    new_status: str
    reason: Optional[str] = None
