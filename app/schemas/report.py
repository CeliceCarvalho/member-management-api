from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AttendanceReportResponse(BaseModel):
    generated_at: datetime
    total_present: int
    attendance_rate: float


class EventAttendanceReportResponse(AttendanceReportResponse):
    event_id: UUID


class MemberAttendanceReportResponse(AttendanceReportResponse):
    member_id: UUID
    total_events: int


class GroupAttendanceReportResponse(AttendanceReportResponse):
    group_id: UUID
    total_members: int
    total_events: int
