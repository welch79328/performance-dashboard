from datetime import date, datetime

from sqlalchemy import String, Integer, Float, Boolean, Date, DateTime, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")  # admin | member
    department: Mapped[str] = mapped_column(String(20), nullable=False, default="pm_rd")  # pm_rd | marketing
    monday_user_id: Mapped[str] = mapped_column(String(50), nullable=True, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class WorkOrderRecord(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    monday_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    client: Mapped[str] = mapped_column(String(100), default="未指定")
    type: Mapped[str] = mapped_column(String(50), default="未指定")
    pm: Mapped[str] = mapped_column(String(100), default="未指定")
    developer: Mapped[str] = mapped_column(String(100), default="未指定")
    tester: Mapped[str] = mapped_column(String(100), default="未指定")
    test_completed_by: Mapped[str] = mapped_column(String(100), default="未指定")
    closed_by: Mapped[str] = mapped_column(String(100), default="未指定")
    assign_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    test_assign_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    test_complete_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    close_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    order_number: Mapped[str] = mapped_column(String(50), default="")
    synced_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class CampaignRecord(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    monday_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(100), default="未指定")
    content_type: Mapped[str] = mapped_column(String(100), default="未指定")
    publish_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_status: Mapped[str] = mapped_column(String(50), default="未指定")
    completion_status: Mapped[str] = mapped_column(String(50), default="未指定")
    platform: Mapped[str] = mapped_column(String(100), default="未指定")
    has_ads: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String(20), default="未指定")
    group_name: Mapped[str] = mapped_column(String(100), default="未指定")
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    material_completeness: Mapped[float] = mapped_column(Float, default=0)
    synced_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    board_name: Mapped[str] = mapped_column(String(100), nullable=False)
    items_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="success")  # success | failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
