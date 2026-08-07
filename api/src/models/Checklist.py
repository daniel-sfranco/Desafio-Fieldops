from typing import Optional
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utils.database import base


class Checklist(base):
    __tablename__ = "flx_checklist_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    workOrderId: Mapped[int] = mapped_column(ForeignKey("flx_work_orders.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    workOrder: Mapped["OS"] = relationship("OS", back_populates="checkList")