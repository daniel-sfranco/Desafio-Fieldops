import datetime
from sqlalchemy import Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.src.database import base

from .OS import OS
from .Usuario import Usuario
from .enums.Status import Status

class Auditoria(base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    workOrderId: Mapped["OS"] = relationship(back_populates="auditList")
    actorId: Mapped["Usuario"] = relationship(back_populates="auditList")
    fromStatus: Mapped[Status] = mapped_column(Enum(Status))
    toStatus: Mapped[Status] = mapped_column(Enum(Status))
    createdAt: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now)