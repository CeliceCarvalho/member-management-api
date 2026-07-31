from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.report import (
    EventAttendanceReportResponse,
    EventMonthlySummaryResponse,
    GroupAttendanceReportResponse,
    MemberAttendanceAnalyticsResponse,
    MemberAttendanceReportResponse,
    MembersSummaryResponse,
)
from app.services import reports as report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/events/monthly-summary", response_model=EventMonthlySummaryResponse)
def generate_event_monthly_summary(
    year: int | None = Query(None, ge=1900, le=3000),
    month: int | None = Query(None, ge=1, le=12),
    db: Session = Depends(get_db),
):
    return report_service.generate_event_monthly_summary(db, year=year, month=month)


@router.get("/members/summary", response_model=MembersSummaryResponse)
def generate_members_summary(db: Session = Depends(get_db)):
    return report_service.generate_members_summary(db)


@router.get("/attendance/by-event/{event_id}", response_model=EventAttendanceReportResponse)
def generate_attendance_report_by_event(event_id: UUID, db: Session = Depends(get_db)):
    return report_service.generate_attendance_report_by_event(db, event_id)


@router.get("/attendance/by-member/{member_id}", response_model=MemberAttendanceReportResponse)
def generate_attendance_report_by_member(member_id: UUID, db: Session = Depends(get_db)):
    return report_service.generate_attendance_report_by_member(db, member_id)


@router.get(
    "/attendance/by-member/{member_id}/analytics",
    response_model=MemberAttendanceAnalyticsResponse,
)
def generate_member_attendance_analytics(
    member_id: UUID,
    months: int = Query(6, ge=1, le=24),
    recent_limit: int = Query(3, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return report_service.generate_member_attendance_analytics(
        db,
        member_id,
        months=months,
        recent_limit=recent_limit,
    )


@router.get("/attendance/by-group/{group_id}", response_model=GroupAttendanceReportResponse)
def generate_attendance_report_by_group(group_id: UUID, db: Session = Depends(get_db)):
    return report_service.generate_attendance_report_by_group(db, group_id)
