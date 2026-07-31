from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.event import Event
from app.models.event_group import EventGroup
from app.models.group import Group
from app.models.group_participation import GroupParticipation
from app.models.member import Member, MemberCategory, MemberStatus
from app.schemas.report import (
    EventMonthlySummaryResponse,
    EventAttendanceReportResponse,
    GroupAttendanceReportResponse,
    MemberAttendanceAnalyticsResponse,
    MemberAttendanceMonthlyAnalytics,
    MemberAttendanceRecentEvent,
    MemberAttendanceReportResponse,
    MembersSummaryResponse,
)

MONTH_LABELS = {
    1: "JAN",
    2: "FEV",
    3: "MAR",
    4: "ABR",
    5: "MAI",
    6: "JUN",
    7: "JUL",
    8: "AGO",
    9: "SET",
    10: "OUT",
    11: "NOV",
    12: "DEZ",
}


def subtract_months(value: date, months: int) -> date:
    month_index = value.month - 1 - months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def build_month_keys(end_date: date, months: int) -> list[tuple[int, int]]:
    first_month = subtract_months(end_date, months - 1)
    keys = []

    for offset in range(months):
        month_index = first_month.month - 1 + offset
        year = first_month.year + month_index // 12
        month = month_index % 12 + 1
        keys.append((year, month))

    return keys


def get_month_range(year: int, month: int) -> tuple[date, date]:
    start_date = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    return start_date, next_month


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


def generate_event_monthly_summary(
    db: Session,
    year: int | None = None,
    month: int | None = None,
) -> EventMonthlySummaryResponse:
    today = date.today()
    target_year = year or today.year
    target_month = month or today.month
    start_date, next_month = get_month_range(target_year, target_month)

    previous_month_date = subtract_months(start_date, 1)
    previous_start_date, previous_next_month = get_month_range(
        previous_month_date.year,
        previous_month_date.month,
    )

    total_events = db.scalar(
        select(func.count())
        .select_from(Event)
        .where(Event.date >= start_date, Event.date < next_month)
    ) or 0

    previous_month_total_events = db.scalar(
        select(func.count())
        .select_from(Event)
        .where(Event.date >= previous_start_date, Event.date < previous_next_month)
    ) or 0

    if previous_month_total_events:
        total_events_change_percent = (
            (total_events - previous_month_total_events)
            / previous_month_total_events
            * 100
        )
    else:
        total_events_change_percent = 100 if total_events else 0

    total_present = db.scalar(
        select(func.count(func.distinct(Attendance.id)))
        .select_from(Attendance)
        .join(Event, Event.id == Attendance.event_id)
        .where(Event.date >= start_date, Event.date < next_month)
    ) or 0

    total_active_members = db.scalar(
        select(func.count()).select_from(Member).where(Member.status == MemberStatus.ACTIVE)
    ) or 0
    expected_attendances = total_events * total_active_members
    average_attendance_rate = (
        total_present / expected_attendances * 100
        if expected_attendances
        else 0
    )

    return EventMonthlySummaryResponse(
        generated_at=datetime.utcnow(),
        year=target_year,
        month=target_month,
        total_events=total_events,
        previous_month_total_events=previous_month_total_events,
        total_events_change_percent=round(total_events_change_percent, 2),
        average_attendance_rate=round(average_attendance_rate, 2),
    )


def generate_members_summary(db: Session) -> MembersSummaryResponse:
    today = date.today()
    month_start, next_month = get_month_range(today.year, today.month)
    week_start = today - timedelta(days=6)

    total_active_members = db.scalar(
        select(func.count()).select_from(Member).where(Member.status == MemberStatus.ACTIVE)
    ) or 0

    new_visitors_this_month = db.scalar(
        select(func.count())
        .select_from(Member)
        .where(
            Member.category == MemberCategory.VISITOR,
            Member.registration_date >= datetime.combine(month_start, datetime.min.time()),
            Member.registration_date < datetime.combine(next_month, datetime.min.time()),
        )
    ) or 0

    weekly_events = db.scalar(
        select(func.count())
        .select_from(Event)
        .where(Event.date >= week_start, Event.date <= today)
    ) or 0

    weekly_present = db.scalar(
        select(func.count(func.distinct(Attendance.id)))
        .select_from(Attendance)
        .join(Event, Event.id == Attendance.event_id)
        .where(Event.date >= week_start, Event.date <= today)
    ) or 0

    expected_weekly_attendances = weekly_events * total_active_members
    weekly_average_attendance_rate = (
        weekly_present / expected_weekly_attendances * 100
        if expected_weekly_attendances
        else 0
    )

    return MembersSummaryResponse(
        generated_at=datetime.utcnow(),
        total_active_members=total_active_members,
        new_visitors_this_month=new_visitors_this_month,
        weekly_average_attendance_rate=round(weekly_average_attendance_rate, 2),
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


def generate_member_attendance_analytics(
    db: Session,
    member_id: UUID,
    months: int = 6,
    recent_limit: int = 3,
) -> MemberAttendanceAnalyticsResponse:
    if not db.get(Member, member_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    latest_event_date = db.scalar(select(func.max(Event.date)).select_from(Event)) or date.today()
    month_keys = build_month_keys(latest_event_date, months)
    start_date = date(month_keys[0][0], month_keys[0][1], 1)

    events = db.scalars(
        select(Event)
        .where(
            Event.date >= start_date,
            Event.date <= latest_event_date,
        )
        .order_by(Event.date.desc(), Event.start_time.desc())
    ).all()

    attendance_event_ids = set(
        db.scalars(
            select(Attendance.event_id)
            .join(Event, Event.id == Attendance.event_id)
            .where(
                Attendance.member_id == member_id,
                Event.date >= start_date,
                Event.date <= latest_event_date,
            )
        ).all()
    )

    monthly_counts = {
        key: {"total_events": 0, "total_present": 0}
        for key in month_keys
    }

    for event in events:
        key = (event.date.year, event.date.month)
        if key not in monthly_counts:
            continue

        monthly_counts[key]["total_events"] += 1
        if event.id in attendance_event_ids:
            monthly_counts[key]["total_present"] += 1

    monthly = []
    for year, month in month_keys:
        counts = monthly_counts[(year, month)]
        total_events = counts["total_events"]
        total_present = counts["total_present"]
        attendance_rate = (total_present / total_events * 100) if total_events else 0
        monthly.append(
            MemberAttendanceMonthlyAnalytics(
                month=MONTH_LABELS[month],
                year=year,
                total_events=total_events,
                total_present=total_present,
                attendance_rate=round(attendance_rate, 2),
            )
        )

    total_events = len(events)
    total_present = len(attendance_event_ids)
    attendance_rate = (total_present / total_events * 100) if total_events else 0

    recent_events = [
        MemberAttendanceRecentEvent(
            event_id=event.id,
            name=event.name,
            date=event.date,
            status="PRESENT" if event.id in attendance_event_ids else "ABSENT",
        )
        for event in events[:recent_limit]
    ]

    return MemberAttendanceAnalyticsResponse(
        member_id=member_id,
        generated_at=datetime.utcnow(),
        attendance_rate=round(attendance_rate, 2),
        total_present=total_present,
        total_events=total_events,
        monthly=monthly,
        recent_events=recent_events,
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
