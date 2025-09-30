from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .shared import PaginationQuery


class PropertyBase(BaseModel):
    name: str
    code: Optional[str] = None
    property_type: Optional[str] = Field(default="residential")
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    owner_id: Optional[int] = None
    manager_id: Optional[int] = None


class PropertyCreate(PropertyBase):
    name: str


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    property_type: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    owner_id: Optional[int] = None
    manager_id: Optional[int] = None


class PropertySummary(BaseModel):
    id: int
    name: str
    code: Optional[str]
    property_type: Optional[str]
    city: Optional[str]
    country: Optional[str]
    occupancy_rate: float
    units_total: int
    units_vacant: int
    pending_kyc: int
    monthly_revenue: float


class PropertyDetail(PropertySummary):
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    notes: Optional[str]
    owner_id: Optional[int]
    manager_id: Optional[int]
    created_at: Optional[datetime]


class PropertyListResponse(BaseModel):
    items: list[PropertySummary]
    total: int


class PropertyQuery(PaginationQuery):
    search: Optional[str] = None
    city: Optional[str] = None
    owner_id: Optional[int] = None
