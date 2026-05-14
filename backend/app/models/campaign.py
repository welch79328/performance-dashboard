from datetime import date

from pydantic import BaseModel, computed_field


class CampaignSubitem(BaseModel):
    id: str
    name: str
    status: str = "未指定"
    has_files: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def subitem_type(self) -> str:
        name_lower = self.name.lower()
        if any(k in name_lower for k in ["copy", "文案"]):
            return "copywriting"
        if any(k in name_lower for k in ["visual", "視覺", "內容"]):
            return "visual"
        return "other"


class Campaign(BaseModel):
    id: str
    name: str
    owner: str = "未指定"
    content_type: str = "未指定"
    publish_date: date | None = None
    review_status: str = "未指定"
    completion_status: str = "未指定"
    platform: str = "未指定"
    has_ads: bool = False
    language: str = "未指定"
    group_name: str = "未指定"
    subitems: list[CampaignSubitem] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_template(self) -> bool:
        return self.review_status == "Cancelled" and self.completion_status == "Paused"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def material_completeness(self) -> float:
        if not self.subitems:
            return 0
        completed = sum(1 for s in self.subitems if s.status == "Done")
        return (completed / len(self.subitems)) * 100
