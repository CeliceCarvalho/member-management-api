from datetime import date, datetime
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


class MemberAttendanceMonthlyAnalytics(BaseModel):
    month: str
    year: int
    total_events: int
    total_present: int
    attendance_rate: float


class MemberAttendanceRecentEvent(BaseModel):
    event_id: UUID
    name: str
    date: date
    status: str


class MemberAttendanceAnalyticsResponse(BaseModel):
    member_id: UUID
    generated_at: datetime
    attendance_rate: float
    total_present: int
    total_events: int
    monthly: list[MemberAttendanceMonthlyAnalytics]
    recent_events: list[MemberAttendanceRecentEvent]


class GroupAttendanceReportResponse(AttendanceReportResponse):
    group_id: UUID
    total_members: int
    total_events: int


class EventMonthlySummaryResponse(BaseModel):
    generated_at: datetime
    year: int
    month: int
    total_events: int
    previous_month_total_events: int
    total_events_change_percent: float
    average_attendance_rate: float


class MembersSummaryResponse(BaseModel):
    generated_at: datetime
    total_active_members: int
    new_visitors_this_month: int
    weekly_average_attendance_rate: float
