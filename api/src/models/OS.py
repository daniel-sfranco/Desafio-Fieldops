from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Enum, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.src.database import base

from .Usuario import Usuario
from .Checklist import Checklist
from .Auditoria import Auditoria
from .enums.Status import Status
from .enums.Priority import Priority


class OS(base):
    __tablename__ = "flx_work_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description = Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Status] = mapped_column(Enum(Status))
    priority: Mapped[Priority] = mapped_column(Enum(Priority))
    resolutionNotes:  Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigneeId: Mapped["Usuario"] = relationship(back_populates="osList")
    teamId: Mapped[str] = mapped_column(String(20))
    version: Mapped[int] = mapped_column(default=1)
    createdAt: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    updatedAt: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)
    checkList: Mapped[List["Checklist"]] = relationship(back_populates="workOrderId")
    auditList: Mapped[List["Auditoria"]] = relationship(back_populates="workOrderId")