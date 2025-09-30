from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..dependencies import get_current_user
from ..models import Lease, MaintenanceRequest, Property, Tenant, Unit
from ..schemas import ActivityFeedItem, DashboardSummary, MetricCard, OccupancyInsight

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    property_count = db.query(func.count(Property.id)).scalar() or 0
    tenant_count = db.query(func.count(Tenant.id)).scalar() or 0
    active_leases = db.query(func.count(Lease.id)).filter(Lease.status == "active").scalar() or 0
    pending_kyc = (
        db.query(func.count(Tenant.id))
        .filter(Tenant.kyc_status.in_(["pending", "submitted", "conditional"]))
        .scalar()
        or 0
    )

    total_revenue = (
        db.query(func.coalesce(func.sum(Lease.rent_amount), 0.0))
        .filter(Lease.status == "active")
        .scalar()
        or 0.0
    )

    # Occupancy insights per property
    occupancy_rows = (
        db.query(Property.id, Property.name, func.count(Unit.id), func.count(func.distinct(Lease.id)))
        .join(Unit, Unit.property_id == Property.id)
        .outerjoin(Lease, (Lease.unit_id == Unit.id) & (Lease.status == "active"))
        .group_by(Property.id, Property.name)
        .order_by(Property.name)
        .all()
    )

    pending_per_property = dict(
        db.query(Unit.property_id, func.count(func.distinct(Tenant.id)))
        .join(Lease, Lease.unit_id == Unit.id)
        .join(Tenant, Tenant.id == Lease.tenant_id)
        .filter(Tenant.kyc_status.in_(["pending", "submitted", "conditional"]))
        .group_by(Unit.property_id)
        .all()
    )

    occupancy_data: list[OccupancyInsight] = []
    for prop_id, name, total_units, active_leases_count in occupancy_rows:
        total_units = total_units or 0
        active_units = active_leases_count or 0
        occupancy_rate = (active_units / total_units) if total_units else 0.0
        occupancy_data.append(
            OccupancyInsight(
                property_id=prop_id,
                property_name=name,
                occupancy_rate=round(occupancy_rate, 2),
                pending_kyc=pending_per_property.get(prop_id, 0),
                vacant_units=max(total_units - active_units, 0),
            )
        )

    recent_maintenance = (
        db.query(MaintenanceRequest)
        .order_by(MaintenanceRequest.created_at.desc())
        .limit(5)
        .all()
    )

    activities: list[ActivityFeedItem] = []
    for record in recent_maintenance:
        activities.append(
            ActivityFeedItem(
                title=record.title,
                subtitle=f"Property ID {record.property_id}",
                timestamp=record.created_at.strftime("%d %b • %H:%M"),
                status=record.status,
            )
        )

    totals = [
        MetricCard(label="Properties", value=float(property_count), formatted=str(property_count), change_pct=None),
        MetricCard(label="Active tenants", value=float(tenant_count), formatted=str(tenant_count), change_pct=None),
        MetricCard(label="Active leases", value=float(active_leases), formatted=str(active_leases), change_pct=None),
        MetricCard(label="Monthly revenue", value=float(total_revenue), formatted=f"KES {total_revenue:,.0f}", change_pct=None),
        MetricCard(label="Pending KYC", value=float(pending_kyc), formatted=str(pending_kyc), change_pct=None),
    ]

    return DashboardSummary(totals=totals, occupancy=occupancy_data, activities=activities)
