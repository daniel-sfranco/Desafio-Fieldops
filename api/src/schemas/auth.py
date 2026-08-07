from typing import Optional
from pydantic import BaseModel, EmailStr
from models.enums.UsuarioRole import UsuarioRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(LoginRequest):
    name: str
    teamId: Optional[str] = None
    role: UsuarioRole = UsuarioRole.TECHNICIAN


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class JWTPayload(BaseModel):
    sub: str
    role: UsuarioRole
    teamId: Optional[str] = None
