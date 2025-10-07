from collections import defaultdict
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config import settings
from ..dependencies import get_current_user, get_current_user_optional, require_roles
from ..core.database import get_db
from ..models import Lease, Property, Tenant, Unit
from ..schemas import (
    PropertyCreate,
    PropertyDetail,
    PropertyListResponse,
    PropertyQuery,
    PropertySummary,
    PropertyUpdate,
    UnitListResponse,
    UnitOut,
)

router = APIRouter(prefix="/properties", tags=["Properties"])


def _aggregate_property_metrics(db: Session, property_ids: List[int]) -> tuple[dict[int, int], dict[int, int], dict[int, int], dict[int, float]]:
    if not property_ids:
        return {}, {}, {}, {}

    total_units = dict(
        db.query(Unit.property_id, func.count(Unit.id))
        .filter(Unit.property_id.in_(property_ids))
        .group_by(Unit.property_id)
        .all()
    )

    occupied_units = dict(
        db.query(Unit.property_id, func.count(func.distinct(Unit.id)))
        .join(Lease, Lease.unit_id == Unit.id)
        .filter(Unit.property_id.in_(property_ids), Lease.status == "active")
        .group_by(Unit.property_id)
        .all()
    )

    pending_kyc = dict(
        db.query(Unit.property_id, func.count(func.distinct(Tenant.id)))
        .join(Lease, Lease.unit_id == Unit.id)
        .join(Tenant, Tenant.id == Lease.tenant_id)
        .filter(
            Unit.property_id.in_(property_ids),
            Tenant.kyc_status.in_(["pending", "submitted", "conditional"]),
        )
        .group_by(Unit.property_id)
        .all()
    )

    monthly_revenue = dict(
        db.query(Unit.property_id, func.coalesce(func.sum(Lease.rent_amount), 0.0))
        .join(Lease, Lease.unit_id == Unit.id)
        .filter(Unit.property_id.in_(property_ids), Lease.status == "active")
        .group_by(Unit.property_id)
        .all()
    )

    return total_units, occupied_units, pending_kyc, monthly_revenue


@router.get("/", response_model=PropertyListResponse)
def list_properties(
    query: PropertyQuery = Depends(),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    if not settings.allow_open_property_management and user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    stmt = db.query(Property)

    if query.search:
        like = f"%{query.search.lower()}%"
        stmt = stmt.filter(func.lower(Property.name).like(like) | func.lower(Property.code).like(like))

    if query.city:
        stmt = stmt.filter(func.lower(Property.city) == query.city.lower())

    if query.owner_id:
        stmt = stmt.filter(Property.owner_id == query.owner_id)

    if user is not None:
        if user.role == "owner":
            stmt = stmt.filter(Property.owner_id == user.id)
        elif user.role == "manager":
            stmt = stmt.filter((Property.manager_id == user.id) | (Property.owner_id == user.id))

    total = stmt.count()

    if query.order == "desc":
        stmt = stmt.order_by(Property.created_at.desc())
    else:
        stmt = stmt.order_by(Property.created_at.asc())

    records = stmt.offset(query.offset).limit(query.limit).all()
    ids = [prop.id for prop in records]

    totals, occupied, pending, revenue = _aggregate_property_metrics(db, ids)

    items: list[PropertySummary] = []
    for prop in records:
        total_units = totals.get(prop.id, 0)
        occupied_units = occupied.get(prop.id, 0)
        units_vacant = max(total_units - occupied_units, 0)
        occupancy_rate = (occupied_units / total_units) if total_units else 0.0
        items.append(
            PropertySummary(
                id=prop.id,
                name=prop.name,
                code=prop.code,
                property_type=prop.property_type,
                city=prop.city,
                country=prop.country,
                occupancy_rate=round(occupancy_rate, 2),
                units_total=total_units,
                units_vacant=units_vacant,
                pending_kyc=pending.get(prop.id, 0),
                monthly_revenue=float(revenue.get(prop.id, 0.0)),
            )
        )

    return PropertyListResponse(items=items, total=total)


@router.post("/", response_model=PropertyDetail, status_code=status.HTTP_201_CREATED)
def create_property(
    payload: PropertyCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    if not settings.allow_open_property_management:
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        if user.role not in {"owner", "manager"}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

    data = payload.dict()
    if user is not None:
        if user.role == "owner" and not data.get("owner_id"):
            data["owner_id"] = user.id
        if user.role == "manager" and not data.get("manager_id"):
            data["manager_id"] = user.id

    prop = Property(**data)
    db.add(prop)
    db.commit()
    db.refresh(prop)

    totals, occupied, pending, revenue = _aggregate_property_metrics(db, [prop.id])

    return PropertyDetail(
        id=prop.id,
        name=prop.name,
        code=prop.code,
        property_type=prop.property_type,
        city=prop.city,
        country=prop.country,
        occupancy_rate=0.0,
        units_total=totals.get(prop.id, 0),
        units_vacant=totals.get(prop.id, 0),
        pending_kyc=pending.get(prop.id, 0),
        monthly_revenue=float(revenue.get(prop.id, 0.0)),
        address_line_1=prop.address_line_1,
        address_line_2=prop.address_line_2,
        notes=prop.notes,
        owner_id=prop.owner_id,
        manager_id=prop.manager_id,
        created_at=prop.created_at,
    )


@router.get("/{property_id}", response_model=PropertyDetail)
def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    if not settings.allow_open_property_management and user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if user is not None and user.role not in {"admin", "viewer"}:
        if user.role == "owner" and prop.owner_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        if user.role == "manager" and prop.manager_id not in {None, user.id} and prop.owner_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    totals, occupied, pending, revenue = _aggregate_property_metrics(db, [property_id])
    total_units = totals.get(property_id, 0)
    occ_units = occupied.get(property_id, 0)
    occupancy_rate = (occ_units / total_units) if total_units else 0.0

    return PropertyDetail(
        id=prop.id,
        name=prop.name,
        code=prop.code,
        property_type=prop.property_type,
        city=prop.city,
        country=prop.country,
        occupancy_rate=round(occupancy_rate, 2),
        units_total=total_units,
        units_vacant=max(total_units - occ_units, 0),
        pending_kyc=pending.get(property_id, 0),
        monthly_revenue=float(revenue.get(property_id, 0.0)),
        address_line_1=prop.address_line_1,
        address_line_2=prop.address_line_2,
        notes=prop.notes,
        owner_id=prop.owner_id,
        manager_id=prop.manager_id,
        created_at=prop.created_at,
    )


@router.patch("/{property_id}", response_model=PropertyDetail)
def update_property(
    property_id: int,
    payload: PropertyUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("owner", "manager")),
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if user.role == "owner" and prop.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    if user.role == "manager" and prop.manager_id not in {None, user.id} and prop.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(prop, key, value)

    db.commit()
    db.refresh(prop)

    totals, occupied, pending, revenue = _aggregate_property_metrics(db, [property_id])
    total_units = totals.get(property_id, 0)
    occ_units = occupied.get(property_id, 0)
    occupancy_rate = (occ_units / total_units) if total_units else 0.0

    return PropertyDetail(
        id=prop.id,
        name=prop.name,
        code=prop.code,
        property_type=prop.property_type,
        city=prop.city,
        country=prop.country,
        occupancy_rate=round(occupancy_rate, 2),
        units_total=total_units,
        units_vacant=max(total_units - occ_units, 0),
        pending_kyc=pending.get(property_id, 0),
        monthly_revenue=float(revenue.get(property_id, 0.0)),
        address_line_1=prop.address_line_1,
        address_line_2=prop.address_line_2,
        notes=prop.notes,
        owner_id=prop.owner_id,
        manager_id=prop.manager_id,
        created_at=prop.created_at,
    )


@router.get("/{property_id}/units", response_model=UnitListResponse)
def list_property_units(
    property_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if user.role == "owner" and prop.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    if user.role == "manager" and prop.manager_id not in {None, user.id} and prop.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    units = (
        db.query(Unit)
        .filter(Unit.property_id == property_id)
        .order_by(Unit.name.asc())
        .all()
    )

    lease_map = defaultdict(lambda: {"lease_id": None, "occupied": False})
    if units:
        unit_ids = [u.id for u in units]
        lease_rows = (
            db.query(Lease.id, Lease.unit_id, Lease.status)
            .filter(Lease.unit_id.in_(unit_ids))
            .all()
        )
        for lease_id, unit_id, status in lease_rows:
            lease_map[unit_id]["lease_id"] = lease_id
            if status == "active":
                lease_map[unit_id]["occupied"] = True

    items = [
        UnitOut(
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
            active_lease_id=lease_map[unit.id]["lease_id"],
            occupied=lease_map[unit.id]["occupied"],
        )
        for unit in units
    ]

    return UnitListResponse(items=items, total=len(items))
