from enum import Enum
import math
from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import asc, delete, desc, func, select

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


def get_user_data(decoded_token: Dict[str, Any]):
    role = decoded_token.get("role")
    user_id = int(decoded_token.get("sub"))
    user_team = decoded_token.get("teamId")
    return role, user_id, user_team


def validate_creator(decoded_token: Dict[str, Any]):
    role = decoded_token.get("role")
    allowed = [UsuarioRole.SUPERVISOR, UsuarioRole.ADMIN, UsuarioRole.SUPERVISOR.value, UsuarioRole.ADMIN.value]
    if role not in allowed:
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

    assignee_role = assignee.role.value if isinstance(assignee.role, Enum) else assignee.role
    if assignee_role != UsuarioRole.TECHNICIAN.value:
        raise FlxException(
            code="FLX_VALIDATION_ERROR",
            message="Usuário designado não é um técnico",
            status_code=422
        )

    token_role = decoded_token.get("role")
    if token_role in [UsuarioRole.SUPERVISOR, UsuarioRole.SUPERVISOR.value]:
        if assignee.teamId != decoded_token.get("teamId"):
            raise FlxException(
                code="FLX_FORBIDDEN",
                message="Usuário designado não é da mesma equipe do supervisor",
                status_code=403
            )


def validate_team(decoded_token: Dict[str, Any], teamId: str):
    token_role = decoded_token.get("role")
    if token_role in [UsuarioRole.SUPERVISOR, UsuarioRole.SUPERVISOR.value]:
        if decoded_token.get("teamId") != teamId:
            raise FlxException(
                code="FLX_FORBIDDEN",
                message="Um supervisor pode criar ordens de serviço apenas para sua própria equipe.",
                status_code=403
            )


def validate_scope(query, sub, role, teamId):
    if role == "technician":
        query = query.where(OS.assigneeId == sub)
    elif role == "supervisor":
        query = query.where(OS.teamId == teamId)
    return query


def apply_filters(query, params):
    if params.status:
        query = query.where(OS.status == params.status)
    if params.priority:
        query = query.where(OS.priority == params.priority)
    return query


def get_ordenation(query, sort_param: str):
    # 1. Dicionário com as colunas permitidas para ordenação
    SORT_FIELDS = {
        "createdAt": OS.createdAt,
        "updatedAt": OS.updatedAt,
        "priority": OS.priority,
        "status": OS.status,
        "title": OS.title,
    }
    # 2. Separa a string em campo e direção (ex: "createdAt:desc")
    if ":" in sort_param:
        field_name, direction = sort_param.split(":", 1)
    else:
        field_name, direction = "createdAt", "desc"
    # 3. Obtém a coluna (se não existir no dicionário, usa OS.createdAt como fallback)
    sort_column = SORT_FIELDS.get(field_name, OS.createdAt)
    # 4. Aplica asc() ou desc()
    if direction.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))
    return query


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


@router.get("/", status_code=status.HTTP_200_OK)
async def list_os(
    params: WorkOrderListQuery = Depends(),
    decoded_token: Dict[str, Any] = Depends(get_current_user), 
    db: Session = Depends(get_db)
    ) -> WorkOrderListResponse:
    role, user_id, user_team = get_user_data(decoded_token)

    total_query = select(func.count(OS.id))
    total_query = validate_scope(total_query, user_id, role, user_team)
    total_query = apply_filters(total_query, params)
    total_items = db.execute(total_query).scalar()

    total_pages = math.ceil(total_items / params.perPage) if total_items > 0 else 1

    query = select(OS).options(selectinload(OS.checkList))
    query = validate_scope(query, user_id, role, user_team)
    query = apply_filters(query, params)
    query = get_ordenation(query, params.sort)
    query = (query.offset((params.page - 1) * params.perPage)
                  .limit(params.perPage))

    items = db.execute(query).scalars().all()

    response = {
        "data": items,
        "meta": {
            "page": params.page,
            "limit": params.perPage,
            "total": total_items,
            "totalPages": total_pages,
        }
    }

    return response


@router.get("/{item_id}", status_code=status.HTTP_200_OK)
async def details_os(
    item_id: int,
    db: Session = Depends(get_db),
    decoded_token: Dict[str, Any] = Depends(get_current_user),
) -> WorkOrderResponse:
    role, user_id, user_team = get_user_data(decoded_token)

    query = select(OS).where(OS.id == item_id).options(selectinload(OS.checkList))
    query = validate_scope(query, user_id, role, user_team)

    item = db.execute(query).scalars().first()
    if item is None:
        raise FlxException(
            code="FLX_NOT_FOUND",
            message="Ordem de serviço não encontrada",
            status_code=404
        )
    
    return item



@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_os(
    item_id: int,
    db: Session = Depends(get_db),
    decoded_token: Dict[str, Any] = Depends(get_current_user),
):
    item = await details_os(item_id, db, decoded_token)
    db.delete(item)
    db.commit()
    return


def otimist_concurrence():
    pass

def status_transition_validation():
    pass


def fields_update(item, data):
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    return item


def generate_audit():
    pass


def commit_item(item, db):
    db.commit()
    db.refresh(item)


@router.patch("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_os(
    item_id: int,
    data: WorkOrderUpdate,
    db: Session = Depends(get_db),
    decoded_token: Dict[str, Any] = Depends(get_current_user),
):
    role, user_id, user_team = get_user_data(decoded_token)

    item = await details_os(item_id, db, decoded_token)
    if data.status is None:
        patched_item = fields_update(item, data)
        commit_item(item, db)

    return patched_item
