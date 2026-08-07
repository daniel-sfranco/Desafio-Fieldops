from enum import Enum


class UsuarioRole(str, Enum):
    TECHNICIAN = "technician"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"
