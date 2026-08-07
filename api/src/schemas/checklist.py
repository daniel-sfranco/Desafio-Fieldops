from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ChecklistItemCreate(BaseModel):
    label: str = Field(..., min_length=1)


class ChecklistItemUpdate(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1)
    completed: Optional[bool] = None


class ChecklistItemResponse(BaseModel):
    id: int
    workOrderId: int
    label: str
    completed: bool

    model_config = ConfigDict(from_attributes=True)
