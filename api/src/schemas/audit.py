from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from models.enums.Status import Status


class WorkOrderEventResponse(BaseModel):
    id: int
    workOrderId: int
    actorId: int
    fromStatus: Optional[Status] = None
    toStatus: Status
    createdAt: datetime

    model_config = ConfigDict(from_attributes=True)
