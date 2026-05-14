from pydantic import BaseModel


class MondayColumnValue(BaseModel):
    id: str
    text: str | None = None
    value: str | None = None


class MondaySubitem(BaseModel):
    id: str
    name: str
    column_values: list[MondayColumnValue] = []


class MondayItem(BaseModel):
    id: str
    name: str
    column_values: list[MondayColumnValue] = []
    subitems: list[MondaySubitem] = []


class MondayUser(BaseModel):
    id: str
    name: str
    email: str
