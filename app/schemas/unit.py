from typing import Optional

from pydantic import BaseModel


class UnitBase(BaseModel):
    property_id: int
    name: str
    floor_label: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    square_feet: Optional[int] = None
    rent_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class UnitCreate(UnitBase):
    pass


class UnitUpdate(BaseModel):
    name: Optional[str] = None
    floor_label: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    square_feet: Optional[int] = None
    rent_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class UnitOut(UnitBase):
    id: int
    property_name: Optional[str] = None
    active_lease_id: Optional[int] = None
    occupied: bool = False


class UnitListResponse(BaseModel):
    items: list[UnitOut]
    total: int
