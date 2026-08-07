from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Enum as SQLEnum, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utils.database import base
from .enums.Status import Status
from .enums.Priority import Priority


class OS(base):
    __tablename__ = "flx_work_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Status] = mapped_column(SQLEnum(Status), default=Status.OPEN, nullable=False)
    priority: Mapped[Priority] = mapped_column(SQLEnum(Priority), default=Priority.LOW, nullable=False)
    resolutionNotes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigneeId: Mapped[Optional[int]] = mapped_column(ForeignKey("flx_users.id"), nullable=True)
    teamId: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    assignee: Mapped[Optional["Usuario"]] = relationship("Usuario", back_populates="osList") # pyright: ignore[reportUndefinedVariable]
    checkList: Mapped[List["Checklist"]] = relationship("Checklist", back_populates="workOrder", cascade="all, delete-orphan")# pyright: ignore[reportUndefinedVariable]
    auditList: Mapped[List["Auditoria"]] = relationship("Auditoria", back_populates="workOrder", cascade="all, delete-orphan")# pyright: ignore[reportUndefinedVariable]