from enum import Enum
import math
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import asc, desc, func, select

from models.Auditoria import Auditoria
from models.Checklist import Checklist
from models.OS import OS
from models.Usuario import Usuario
from models.enums.Status import Status
from models.enums.Priority import Priority
from models.enums.UsuarioRole import UsuarioRole
from schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderResponse,
    WorkOrderListQuery,
    WorkOrderListResponse,
)
from schemas.audit import WorkOrderEventResponse
from schemas.checklist import ChecklistItemUpdate, ChecklistItemResponse

from utils.database import get_db
from utils.exceptions import FlxException
from utils.security import get_current_user
from utils.webhook import notify

router = APIRouter(
    prefix="/work-orders",
    tags=["Work Order Module"]
)


def get_user_data(decoded_token: Dict[str, Any]):
    role = decoded_token.get("role")
    user_id = int(decoded_token.get("sub"))
    user_team = decoded_token.get("teamId")
    return role, user_id, user_team


def validate_creator(role: str):
    allowed = [UsuarioRole.SUPERVISOR, UsuarioRole.ADMIN, UsuarioRole.SUPERVISOR.value, UsuarioRole.ADMIN.value]
    if role not in allowed:
        raise FlxException(
            code="FLX_FORBIDDEN",
            message="Criador da ordem de serviço deve ser um supervisor ou um administrador do sistema.",
            status_code=403
        )


def validate_assignee(assignee: Usuario, role: str, teamId: str):
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

    if role in [UsuarioRole.SUPERVISOR, UsuarioRole.SUPERVISOR.value]:
        if assignee.teamId != teamId:
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


def validate_scope(query, sub: int, role: str, teamId: str):
    if role == UsuarioRole.TECHNICIAN.value or role == UsuarioRole.TECHNICIAN:
        query = query.where(OS.assigneeId == sub)
    elif role == UsuarioRole.SUPERVISOR.value or role == UsuarioRole.SUPERVISOR:
        query = query.where(OS.teamId == teamId)
    return query


def apply_filters(query, params: WorkOrderListQuery):
    if params.status:
        query = query.where(OS.status == params.status)
    if params.priority:
        query = query.where(OS.priority == params.priority)
    return query


def get_ordenation(query, sort_param: str):
    SORT_FIELDS = {
        "createdAt": OS.createdAt,
        "updatedAt": OS.updatedAt,
        "priority": OS.priority,
        "status": OS.status,
        "title": OS.title,
    }
    if ":" in sort_param:
        field_name, direction = sort_param.split(":", 1)
    else:
        field_name, direction = "createdAt", "desc"
    sort_column = SORT_FIELDS.get(field_name, OS.createdAt)
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
    role, user_id, user_team = get_user_data(decoded_token)
    validate_creator(role)

    validate_team(decoded_token, os.teamId)

    if os.assigneeId:
        assignee_query = select(Usuario).where(Usuario.id == os.assigneeId)
        assignee = db.execute(assignee_query).scalars().first()
        validate_assignee(assignee, role, user_team)

    new_os = OS(
        title=os.title,
        description=os.description,
        status=Status.OPEN,
        priority=os.priority,
        assigneeId=os.assigneeId,
        teamId=os.teamId,
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
    total_items = db.execute(total_query).scalar() or 0

    total_pages = math.ceil(total_items / params.perPage) if total_items > 0 else 0

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


@router.get("/{item_id}/history", status_code=status.HTTP_200_OK)
async def get_os_history(
    item_id: int,
    db: Session = Depends(get_db),
    decoded_token: Dict[str, Any] = Depends(get_current_user),
) -> List[WorkOrderEventResponse]:
    item = await details_os(item_id, db, decoded_token)
    
    query = select(Auditoria).where(Auditoria.workOrderId == item.id).order_by(asc(Auditoria.createdAt))
    events = db.execute(query).scalars().all()
    return events


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


def validate_assignee_patch(data: WorkOrderUpdate, role: str, user_team: str, db: Session):
    if data.assigneeId is not None:
        if role in [UsuarioRole.TECHNICIAN, UsuarioRole.TECHNICIAN.value]:
            raise FlxException(
                code="FLX_FORBIDDEN",
                message="Técnicos não possuem permissão para reatribuir ordens de serviço.",
                status_code=403
            )
        assignee_query = select(Usuario).where(Usuario.id == data.assigneeId)
        assignee = db.execute(assignee_query).scalars().first()
        validate_assignee(assignee, role, user_team)


def otimist_concurrence(item: OS, data: WorkOrderUpdate):
    if data.version is None or item.version != data.version:
        raise FlxException(
            code="FLX_CONCURRENT_UPDATE",
            message="Houveram outras atualizações a esse registro, e houve conflito. Tente novamente.",
            status_code=409
        )


def status_transition_validation(item: OS, data: WorkOrderUpdate, role: str):
    prev = item.status.value if isinstance(item.status, Enum) else item.status
    next_status = data.status.value if isinstance(data.status, Enum) else data.status

    if prev == next_status:
        return

    if prev == 'open' and next_status == 'in_progress':
        effective_assignee = data.assigneeId if data.assigneeId is not None else item.assigneeId
        if effective_assignee is None:
            raise FlxException(
                code="FLX_INVALID_STATUS_TRANSITION",
                message="Uma ordem de serviço em andamento deve ter um técnico designado.",
                status_code=422
            )
    elif prev == 'in_progress' and next_status == 'done':
        priority_val = item.priority.value if isinstance(item.priority, Enum) else item.priority
        if priority_val == Priority.HIGH.value and role in [UsuarioRole.TECHNICIAN, UsuarioRole.TECHNICIAN.value]:
            raise FlxException(
                code="FLX_FORBIDDEN",
                message="Uma ordem de serviço de alta prioridade só pode ser concluída por um supervisor ou administrador.",
                status_code=403
            )
        notes = data.resolutionNotes or item.resolutionNotes
        if not notes or len(notes.strip()) < 10:
            raise FlxException(
                code="FLX_INVALID_STATUS_TRANSITION",
                message="Uma ordem de serviço só pode ser concluída com a inclusão de notas sobre a resolução da mesma (mín. 10 caracteres).",
                status_code=422
            )
    elif prev == 'in_progress' and next_status == 'open':
        open_tasks = [i for i in item.checkList if not i.completed]
        if len(open_tasks) == 0:
            raise FlxException(
                code="FLX_INVALID_STATUS_TRANSITION",
                message="Uma ordem de serviço só pode ser reaberta caso alguma tarefa do checklist não tenha sido cumprida.",
                status_code=422
            )
    else:
        raise FlxException(
            code="FLX_INVALID_STATUS_TRANSITION",
            message="A mudança de status solicitada não é permitida.",
            status_code=422
        )


def fields_update(item: OS, data: WorkOrderUpdate, role: str):
    if role in [UsuarioRole.TECHNICIAN, UsuarioRole.TECHNICIAN.value]:
        if data.priority is not None:
            raise FlxException(
                code="FLX_FORBIDDEN",
                message="Uma ordem de serviço não pode ter sua prioridade alterada por um técnico.",
                status_code=403
            )
        if data.title is not None or data.description is not None:
            raise FlxException(
                code="FLX_FORBIDDEN",
                message="Técnicos não possuem permissão para alterar o título ou a descrição da ordem de serviço.",
                status_code=403
            )

    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("version", None)
    for key, value in update_data.items():
        setattr(item, key, value)
    item.version += 1
    return item


def generate_audit(item: OS, from_status: str, to_status: str, user_id: int, db: Session):
    audit = Auditoria(
        workOrderId=item.id,
        actorId=user_id,
        fromStatus=from_status,
        toStatus=to_status,
    )
    db.add(audit)
    return audit


def commit_item(item: OS, db: Session):
    db.commit()
    db.refresh(item)


@router.patch("/{item_id}", status_code=status.HTTP_200_OK)
async def patch_os(
    item_id: int,
    data: WorkOrderUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    decoded_token: Dict[str, Any] = Depends(get_current_user),
) -> WorkOrderResponse:
    role, user_id, user_team = get_user_data(decoded_token)

    item = await details_os(item_id, db, decoded_token)
    validate_assignee_patch(data, role, user_team, db)

    prev_status = item.status.value if isinstance(item.status, Enum) else item.status

    if data.status is not None:
        otimist_concurrence(item, data)
        status_transition_validation(item, data, role)

    patched_item = fields_update(item, data, role)

    if data.status is not None:
        new_status = data.status.value if isinstance(data.status, Enum) else data.status
        if new_status != prev_status:
            audit = generate_audit(item, prev_status, new_status, user_id, db)
            commit_item(item, db)
            background_tasks.add_task(notify, audit)
        else:
            commit_item(item, db)
    else:
        commit_item(item, db)
    return patched_item


@router.patch("/{item_id}/checklist/{checklist_id}", status_code=status.HTTP_200_OK)
async def update_checklist_item(
    item_id: int,
    checklist_id: int,
    data: ChecklistItemUpdate,
    db: Session = Depends(get_db),
    decoded_token: Dict[str, Any] = Depends(get_current_user),
) -> ChecklistItemResponse:
    item = await details_os(item_id, db, decoded_token)

    checklist_item = next((c for c in item.checkList if c.id == checklist_id), None)
    if not checklist_item:
        raise FlxException(
            code="FLX_NOT_FOUND",
            message="Item de checklist não encontrado",
            status_code=404
        )

    if data.label is not None:
        checklist_item.label = data.label
    if data.completed is not None:
        checklist_item.completed = data.completed

    db.commit()
    db.refresh(checklist_item)
    return checklist_item
