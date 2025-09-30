from typing import List
from pydantic import BaseModel


class MetricCard(BaseModel):
    label: str
    value: float
    formatted: str
    change_pct: float | None = None


class OccupancyInsight(BaseModel):
    property_id: int
    property_name: str
    occupancy_rate: float
    pending_kyc: int
    vacant_units: int


class ActivityFeedItem(BaseModel):
    title: str
    subtitle: str
    timestamp: str
    status: str


class DashboardSummary(BaseModel):
    totals: List[MetricCard]
    occupancy: List[OccupancyInsight]
    activities: List[ActivityFeedItem]
