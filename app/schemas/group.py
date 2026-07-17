from datetime import time as TimeType
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.group import GroupType


class GroupBase(BaseModel):
    name: str
    type: GroupType
    weekday: str | None = None
    time: TimeType | None = None
    recurring_location: str | None = None
    leader_id: UUID | None = None
    co_leader_id: UUID | None = None


class GroupCreate(GroupBase):
    member_ids: list[UUID] = Field(default_factory=list)


class GroupUpdate(BaseModel):
    name: str | None = None
    type: GroupType | None = None
    weekday: str | None = None
    time: TimeType | None = None
    recurring_location: str | None = None
    leader_id: UUID | None = None
    co_leader_id: UUID | None = None
    active: bool | None = None
    member_ids: list[UUID] | None = None


class GroupResponse(GroupBase):
    id: UUID
    active: bool
    member_ids: list[UUID] = Field(default_factory=list)

    model_config = {"from_attributes": True}
