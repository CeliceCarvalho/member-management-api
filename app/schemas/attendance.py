from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AttendanceCreate(BaseModel):
    event_id: UUID
    member_id: UUID
    note: str | None = None


class EventAttendanceCreate(BaseModel):
    member_id: UUID
    note: str | None = None


class AttendanceUpdate(BaseModel):
    note: str | None = None


class AttendanceResponse(BaseModel):
    id: UUID
    event_id: UUID
    member_id: UUID
    checked_in_at: datetime
    note: str | None

    model_config = {"from_attributes": True}
