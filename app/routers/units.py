from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..dependencies import get_current_user, require_roles
from ..models import Lease, Property, Unit
from ..schemas import UnitCreate, UnitOut, UnitUpdate

router = APIRouter(prefix="/units", tags=["Units"])


def _authorize(user, prop: Property):
    if user.role == "owner" and prop.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    if user.role == "manager" and prop.manager_id not in {None, user.id} and prop.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")


@router.post("/", response_model=UnitOut, status_code=status.HTTP_201_CREATED)
def create_unit(
    payload: UnitCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager")),
):
    prop = db.query(Property).filter(Property.id == payload.property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    _authorize(user, prop)

    unit = Unit(**payload.dict())
    db.add(unit)
    db.commit()
    db.refresh(unit)

    active_lease = (
        db.query(Lease)
        .filter(Lease.unit_id == unit.id, Lease.status == "active")
        .first()
    )

    return UnitOut(
        id=unit.id,
        property_id=unit.property_id,
        name=unit.name,
        floor_label=unit.floor_label,
        bedrooms=unit.bedrooms,
        bathrooms=unit.bathrooms,
        square_feet=unit.square_feet,
        rent_amount=float(unit.rent_amount or 0),
        status=unit.status,
        notes=unit.notes,
        property_name=prop.name,
        active_lease_id=active_lease.id if active_lease else None,
        occupied=bool(active_lease),
    )


@router.patch("/{unit_id}", response_model=UnitOut)
def update_unit(
    unit_id: int,
    payload: UnitUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager")),
):
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    prop = db.query(Property).filter(Property.id == unit.property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent property missing")

    _authorize(user, prop)

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(unit, key, value)

    db.commit()
    db.refresh(unit)

    active_lease = (
        db.query(Lease)
        .filter(Lease.unit_id == unit.id, Lease.status == "active")
        .first()
    )

    return UnitOut(
        id=unit.id,
        property_id=unit.property_id,
        name=unit.name,
        floor_label=unit.floor_label,
        bedrooms=unit.bedrooms,
        bathrooms=unit.bathrooms,
        square_feet=unit.square_feet,
        rent_amount=float(unit.rent_amount or 0),
        status=unit.status,
        notes=unit.notes,
        property_name=prop.name,
        active_lease_id=active_lease.id if active_lease else None,
        occupied=bool(active_lease),
    )
