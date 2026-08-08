from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.enums.Priority import Priority
from models.enums.Status import Status
from .checklist import ChecklistItemCreate, ChecklistItemResponse


class WorkOrderCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    priority: Priority = Priority.LOW
    teamId: str = Field(..., min_length=1)
    assigneeId: Optional[int] = None
    initialChecklist: List[ChecklistItemCreate] = Field(..., min_length=1)


class WorkOrderUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    assigneeId: Optional[int] = None
    resolutionNotes: Optional[str] = None
    version: Optional[int] = None

    @model_validator(mode="after")
    def validate_status_rules(self) -> "WorkOrderUpdate":
        if self.status is not None:
            if self.version is None:
                raise ValueError(
                    "O campo 'version' é obrigatório ao alterar o status."
                )

            if self.status == Status.DONE:
                notes = self.resolutionNotes
                if not notes or len(notes.strip()) < 10:
                    raise ValueError(
                        "O campo 'resolutionNotes' deve conter no mínimo 10 "
                        "caracteres para concluir a OS."
                    )
        return self


class WorkOrderResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: Status
    priority: Priority
    resolutionNotes: Optional[str] = None
    assigneeId: Optional[int] = None
    teamId: str
    version: int
    createdAt: datetime
    updatedAt: datetime
    checklist: List[ChecklistItemResponse] = Field(
        default_factory=list, alias="checkList"
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class WorkOrderListQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    perPage: int = Field(default=20, ge=1, le=100)
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    sort: str = "createdAt:desc"


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    totalPages: int

class WorkOrderListResponse(BaseModel):
    data: List[WorkOrderResponse]
    meta: PaginationMeta