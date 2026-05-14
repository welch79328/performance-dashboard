from datetime import date

from pydantic import BaseModel, computed_field


class WorkOrder(BaseModel):
    id: str
    name: str
    client: str = "未指定"
    type: str = "未指定"
    pm: str = "未指定"
    developer: str = "未指定"
    tester: str = "未指定"
    test_completed_by: str = "未指定"
    closed_by: str = "未指定"
    assign_date: date | None = None
    test_assign_date: date | None = None
    test_complete_date: date | None = None
    close_date: date | None = None
    order_number: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> str:
        if self.close_date:
            return "已結案"
        if self.test_assign_date:
            return "測試中"
        if self.assign_date:
            return "開發中"
        return "未指派"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_days(self) -> float | None:
        if self.assign_date and self.close_date:
            return (self.close_date - self.assign_date).days
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def dev_days(self) -> float | None:
        if self.assign_date and self.test_assign_date:
            return (self.test_assign_date - self.assign_date).days
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def test_days(self) -> float | None:
        if self.test_assign_date and self.close_date:
            return (self.close_date - self.test_assign_date).days
        return None
