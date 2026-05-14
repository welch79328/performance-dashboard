from datetime import date

from pydantic import BaseModel


# === 維度 1：工作量 ===

class PersonWorkload(BaseModel):
    user_name: str
    pm_count: int = 0
    dev_count: int = 0
    test_count: int = 0
    total_count: int = 0
    in_progress_count: int = 0


class MarketingWorkload(BaseModel):
    user_name: str
    content_count: int = 0
    platform_distribution: dict[str, int] = {}
    content_type_distribution: dict[str, int] = {}
    cross_platform_count: int = 0
    scheduled_count: int = 0
    posts_per_week: float = 0


# === 維度 2：流程效率 ===

class EfficiencyMetrics(BaseModel):
    avg_total_days: float = 0
    avg_dev_days: float = 0
    avg_test_days: float = 0
    close_rate: float = 0
    stalled_rate: float = 0
    stalled_orders: list[str] = []


class EfficiencyByType(BaseModel):
    type_name: str
    count: int = 0
    avg_total_days: float = 0
    avg_dev_days: float = 0
    avg_test_days: float = 0
    close_rate: float = 0


class MarketingEfficiency(BaseModel):
    completion_rate: float = 0
    weekly_std_dev: float = 0
    material_completeness: float = 0


# === 維度 3：專案排程 ===

class GanttItem(BaseModel):
    id: str
    name: str
    client: str
    developer: str
    start_date: date
    end_date: date | None = None
    status: str


class HeatmapCell(BaseModel):
    label: str
    week: str
    count: int


class AgingOrder(BaseModel):
    id: str
    name: str
    client: str
    developer: str
    assign_date: date
    days_open: int
    severity: str


# === 維度 4：品質間接指標 ===

class QualityMetrics(BaseModel):
    bug_recurrence: dict[str, int] = {}
    change_density: float = 0
    change_density_trend: list[float] = []


# === 彙總 ===

class TeamKPI(BaseModel):
    department: str
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    close_rate: float = 0
    avg_processing_days: float = 0
    member_workloads: list[PersonWorkload | MarketingWorkload] = []
    efficiency: EfficiencyMetrics | MarketingEfficiency | None = None
    efficiency_by_type: list[EfficiencyByType] = []
    quality: QualityMetrics | None = None
    type_distribution: dict[str, int] = {}
    client_distribution: dict[str, int] = {}


class WeeklyTrend(BaseModel):
    week_start: str
    week_end: str
    task_count: int = 0
    close_rate: float = 0
    avg_days: float = 0
    bug_count: int = 0
    change_count: int = 0


class DateRangeRequest(BaseModel):
    preset: str | None = None
    start: date | None = None
    end: date | None = None
    department: str = "all"
