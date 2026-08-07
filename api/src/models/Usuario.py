from typing import List, Optional
from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utils.database import base
from .enums.UsuarioRole import UsuarioRole


class Usuario(base):
    __tablename__ = "flx_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    teamId: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    role: Mapped[UsuarioRole] = mapped_column(SQLEnum(UsuarioRole), nullable=False)

    osList: Mapped[List["OS"]] = relationship("OS", back_populates="assignee")# pyright: ignore[reportUndefinedVariable]
    auditList: Mapped[List["Auditoria"]] = relationship("Auditoria", back_populates="actor")# pyright: ignore[reportUndefinedVariable]

    def __init__(self, email, password, name, teamId, role):
        self.email = email
        self.password = password
        self.name = name
        self.teamId = teamId
        self.role = role
