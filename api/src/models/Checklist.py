from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.src.database import base

from .OS import OS

class Checklist(base):
    __tablename__ = "flx_checklist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    workOrderId: Mapped["OS"] = relationship(back_populates="checkList")
    label: Mapped[str] = mapped_column(String(100))
    done: Mapped[bool] = mapped_column(Boolean, default=False)