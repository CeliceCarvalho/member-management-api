from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.report import (
    EventAttendanceReportResponse,
    GroupAttendanceReportResponse,
    MemberAttendanceReportResponse,
)
from app.services import reports as report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/attendance/by-event/{event_id}", response_model=EventAttendanceReportResponse)
def generate_attendance_report_by_event(event_id: UUID, db: Session = Depends(get_db)):
    return report_service.generate_attendance_report_by_event(db, event_id)


@router.get("/attendance/by-member/{member_id}", response_model=MemberAttendanceReportResponse)
def generate_attendance_report_by_member(member_id: UUID, db: Session = Depends(get_db)):
    return report_service.generate_attendance_report_by_member(db, member_id)


@router.get("/attendance/by-group/{group_id}", response_model=GroupAttendanceReportResponse)
def generate_attendance_report_by_group(group_id: UUID, db: Session = Depends(get_db)):
    return report_service.generate_attendance_report_by_group(db, group_id)
