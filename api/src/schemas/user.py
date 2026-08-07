from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from models.enums.UsuarioRole import UsuarioRole


class UsuarioBase(BaseModel):
    email: EmailStr
    name: str
    teamId: Optional[str] = None
    role: UsuarioRole


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    name: Optional[str] = None
    teamId: Optional[str] = None
    role: Optional[UsuarioRole] = None


class UsuarioResponse(UsuarioBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
