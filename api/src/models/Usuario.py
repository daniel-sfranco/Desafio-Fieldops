import enum
from typing import List
from sqlalchemy import String, Enum 
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.src.database import base

from .OS import OS
from .Auditoria import Auditoria

class PapelUsuario(enum.Enum):
    TECHNICIAN = 'technician'
    SUPERVISOR = 'supervisor'
    ADMIN = 'admin'

class Usuario(base):
    __tablename__ = "flx_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    teamId: Mapped[str] = mapped_column(String(20))
    role: Mapped[PapelUsuario] = mapped_column(Enum(PapelUsuario))
    osList: Mapped[List["OS"]] = relationship(back_populates="osList")
    auditList: Mapped[List["Auditoria"]] = relationship(back_populates="actorId")