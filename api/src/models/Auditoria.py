from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Enum as SQLEnum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utils.database import base
from .enums.Status import Status

if TYPE_CHECKING:
    from models.OS import OS
    from models.Usuario import Usuario


class Auditoria(base):
    __tablename__ = "flx_work_order_events"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, index=True
    )
    workOrderId: Mapped[int] = mapped_column(
        ForeignKey("flx_work_orders.id", ondelete="CASCADE"), nullable=False
    )
    actorId: Mapped[int] = mapped_column(
        ForeignKey("flx_users.id"), nullable=False
    )
    fromStatus: Mapped[Optional[Status]] = mapped_column(
        SQLEnum(Status), nullable=True
    )
    toStatus: Mapped[Status] = mapped_column(SQLEnum(Status), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    workOrder: Mapped["OS"] = relationship("OS", back_populates="auditList")
    actor: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="auditList"
    )
