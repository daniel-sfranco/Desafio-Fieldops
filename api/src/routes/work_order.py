from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from models.Checklist import Checklist
from models.OS import OS
from models.Usuario import Usuario
from models.enums.Status import Status
from models.enums.UsuarioRole import UsuarioRole
from schemas.work_order import *

from utils.database import get_db
from utils.exceptions import FlxException
from utils.security import get_current_user

router = APIRouter (
    prefix="/work-orders",
    tags=["Work Order Module"]
)


def validate_creator(decoded_token: Dict[str, Any]):
    if decoded_token["role"] not in [UsuarioRole.SUPERVISOR, UsuarioRole.ADMIN]:
        raise FlxException(
            code="FLX_FORBIDDEN",
            message="Criador da ordem de serviço deve ser um supervisor ou um administrador do sistema.",
            status_code=403
        )


def validate_assignee(assignee: Usuario, decoded_token: Dict[str, Any], db: Session = Depends(get_db)):
    if not assignee:
        raise FlxException(
            code="FLX_VALIDATION_ERROR",
            message="Usuário designado não existe",
            status_code=422
        )

    if assignee.role != UsuarioRole.TECHNICIAN:
        raise FlxException(
            code="FLX_VALIDATION_ERROR",
            message="Usuário designado não é um técnico",
            status_code=422
        )

    if decoded_token["role"] == UsuarioRole.SUPERVISOR:
        if assignee.teamId != decoded_token["teamId"]:
            raise FlxException(
                code="FLX_FORBIDDEN",
                message="Usuário designado não é da mesma equipe do supervisor",
                status_code=403
            )



def validate_team(decoded_token: Dict[str, Any], teamId: str):
    if decoded_token["role"] == UsuarioRole.SUPERVISOR:
        if decoded_token["teamId"] != teamId:
            raise FlxException(
                code="FLX_FORBIDDEN",
                message="Um supervisor pode criar ordens de serviço apenas para sua própria equipe.",
                status_code=403
            )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_os(
    os: WorkOrderCreate, 
    decoded_token: Dict[str, Any] = Depends(get_current_user), 
    db: Session = Depends(get_db)
    ) -> WorkOrderResponse:
    validate_creator(decoded_token)

    validate_team(decoded_token, os.teamId)

    if os.assigneeId:
        assignee_query = select(Usuario).where(Usuario.id == os.assigneeId)
        assignee = db.execute(assignee_query).scalars().first()
        validate_assignee(assignee, decoded_token)

    new_os = OS (
        title = os.title,
        description = os.description,
        status = Status.OPEN,
        priority = os.priority,
        assigneeId = os.assigneeId,
        teamId = os.teamId,
    )

    for item in os.initialChecklist:
        new_os.checkList.append(Checklist(
            label=item.label,
            completed=False,
        ))

    db.add(new_os)
    db.commit()
    db.refresh(new_os)

    return new_os
