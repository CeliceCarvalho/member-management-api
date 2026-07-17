from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GroupParticipationCreate(BaseModel):
    member_id: UUID
    group_id: UUID


class GroupParticipationResponse(BaseModel):
    id: UUID
    member_id: UUID
    group_id: UUID
    joined_at: datetime
    left_at: datetime | None
    active: bool

    model_config = {"from_attributes": True}
