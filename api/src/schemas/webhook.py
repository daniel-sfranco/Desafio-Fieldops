from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from models.enums.Status import Status


class WebhookEventPayload(BaseModel):
    eventId: str
    workOrderId: int
    fromStatus: Optional[Status] = None
    toStatus: Status
    actorId: int
    occurredAt: datetime

    model_config = ConfigDict(from_attributes=True)
