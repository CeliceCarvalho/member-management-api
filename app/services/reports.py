from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.event import Event
from app.models.event_group import EventGroup
from app.models.group import Group
from app.models.group_participation import GroupParticipation
from app.models.member import Member, MemberStatus
from app.schemas.report import (
    EventAttendanceReportResponse,
    GroupAttendanceReportResponse,
    MemberAttendanceReportResponse,
)


def generate_attendance_report_by_event(
    db: Session,
    event_id: UUID,
) -> EventAttendanceReportResponse:
    if not db.get(Event, event_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    total_present = db.scalar(
        select(func.count()).select_from(Attendance).where(Attendance.event_id == event_id)
    ) or 0
    total_active_members = db.scalar(
        select(func.count()).select_from(Member).where(Member.status == MemberStatus.ACTIVE)
    ) or 0
    attendance_rate = (total_present / total_active_members * 100) if total_active_members else 0

    return EventAttendanceReportResponse(
        event_id=event_id,
        generated_at=datetime.utcnow(),
        total_present=total_present,
        attendance_rate=round(attendance_rate, 2),
    )


def generate_attendance_report_by_member(
    db: Session,
    member_id: UUID,
) -> MemberAttendanceReportResponse:
    if not db.get(Member, member_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    total_present = db.scalar(
        select(func.count()).select_from(Attendance).where(Attendance.member_id == member_id)
    ) or 0
    total_events = db.scalar(select(func.count()).select_from(Event)) or 0
    attendance_rate = (total_present / total_events * 100) if total_events else 0

    return MemberAttendanceReportResponse(
        member_id=member_id,
        generated_at=datetime.utcnow(),
        total_present=total_present,
        total_events=total_events,
        attendance_rate=round(attendance_rate, 2),
    )


def generate_attendance_report_by_group(
    db: Session,
    group_id: UUID,
) -> GroupAttendanceReportResponse:
    if not db.get(Group, group_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

    total_members = db.scalar(
        select(func.count())
        .select_from(GroupParticipation)
        .where(
            GroupParticipation.group_id == group_id,
            GroupParticipation.active.is_(True),
        )
    ) or 0

    total_events = db.scalar(
        select(func.count()).select_from(EventGroup).where(EventGroup.group_id == group_id)
    ) or 0

    total_present = db.scalar(
        select(func.count(distinct(Attendance.id)))
        .select_from(Attendance)
        .join(EventGroup, EventGroup.event_id == Attendance.event_id)
        .join(GroupParticipation, GroupParticipation.member_id == Attendance.member_id)
        .where(
            EventGroup.group_id == group_id,
            GroupParticipation.group_id == group_id,
            GroupParticipation.active.is_(True),
        )
    ) or 0

    expected_attendances = total_members * total_events
    attendance_rate = (total_present / expected_attendances * 100) if expected_attendances else 0

    return GroupAttendanceReportResponse(
        group_id=group_id,
        generated_at=datetime.utcnow(),
        total_present=total_present,
        total_members=total_members,
        total_events=total_events,
        attendance_rate=round(attendance_rate, 2),
    )
