from datetime import date as DateType, datetime, time as TimeType
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.event import EventStatus, Weekday


class EventBase(BaseModel):
    name: str
    date: DateType
    start_time: TimeType
    end_time: TimeType | None = None
    location: str | None = None
    recurring: bool = False
    weekdays: list[Weekday] = Field(default_factory=list)
    status: EventStatus = EventStatus.SCHEDULED


class EventCreate(EventBase):
    group_ids: list[UUID] = Field(default_factory=list)
    attendance_member_ids: list[UUID] = Field(default_factory=list)


class EventUpdate(BaseModel):
    name: str | None = None
    date: DateType | None = None
    start_time: TimeType | None = None
    end_time: TimeType | None = None
    location: str | None = None
    recurring: bool | None = None
    weekdays: list[Weekday] | None = None
    status: EventStatus | None = None
    group_ids: list[UUID] | None = None
    attendance_member_ids: list[UUID] | None = None


class EventResponse(EventBase):
    id: UUID
    created_at: datetime
    group_ids: list[UUID] = Field(default_factory=list)
    attendance_member_ids: list[UUID] = Field(default_factory=list)

    model_config = {"from_attributes": True}
