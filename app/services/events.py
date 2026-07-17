from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.event import Event
from app.models.event_group import EventGroup
from app.models.group import Group
from app.models.member import Member
from app.schemas.attendance import AttendanceResponse, EventAttendanceCreate
from app.schemas.event import EventCreate, EventResponse, EventUpdate


def get_event_group_ids(db: Session, event_id: UUID) -> list[UUID]:
    return db.scalars(select(EventGroup.group_id).where(EventGroup.event_id == event_id)).all()


def get_attendance_member_ids(db: Session, event_id: UUID) -> list[UUID]:
    return db.scalars(select(Attendance.member_id).where(Attendance.event_id == event_id)).all()


def build_event_response(db: Session, event: Event) -> EventResponse:
    return EventResponse.model_validate(event).model_copy(
        update={
            "group_ids": get_event_group_ids(db, event.id),
            "attendance_member_ids": get_attendance_member_ids(db, event.id),
        }
    )


def validate_group_ids(db: Session, group_ids: list[UUID]) -> None:
    if not group_ids:
        return

    existing_group_ids = set(db.scalars(select(Group.id).where(Group.id.in_(group_ids))).all())
    if set(group_ids) - existing_group_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more groups were not found.",
        )


def validate_member_ids(db: Session, member_ids: list[UUID]) -> None:
    if not member_ids:
        return

    existing_member_ids = set(db.scalars(select(Member.id).where(Member.id.in_(member_ids))).all())
    if set(member_ids) - existing_member_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more members were not found.",
        )


def sync_event_groups(db: Session, event_id: UUID, group_ids: list[UUID]) -> None:
    validate_group_ids(db, group_ids)

    target_group_ids = set(group_ids)
    current_event_groups = db.scalars(
        select(EventGroup).where(EventGroup.event_id == event_id)
    ).all()
    current_group_ids = {event_group.group_id for event_group in current_event_groups}

    for event_group in current_event_groups:
        if event_group.group_id not in target_group_ids:
            db.delete(event_group)

    for group_id in target_group_ids - current_group_ids:
        db.add(EventGroup(event_id=event_id, group_id=group_id))


def sync_event_attendances(db: Session, event_id: UUID, member_ids: list[UUID]) -> None:
    validate_member_ids(db, member_ids)

    target_member_ids = set(member_ids)
    current_attendances = db.scalars(
        select(Attendance).where(Attendance.event_id == event_id)
    ).all()
    current_member_ids = {attendance.member_id for attendance in current_attendances}

    for attendance in current_attendances:
        if attendance.member_id not in target_member_ids:
            db.delete(attendance)

    for member_id in target_member_ids - current_member_ids:
        db.add(Attendance(event_id=event_id, member_id=member_id))


def create_event(db: Session, event_data: EventCreate) -> EventResponse:
    create_data = event_data.model_dump(exclude={"group_ids", "attendance_member_ids"})
    event = Event(**create_data)
    db.add(event)

    try:
        db.flush()
        sync_event_groups(db, event.id, event_data.group_ids)
        sync_event_attendances(db, event.id, event_data.attendance_member_ids)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate attendance for this event.",
        ) from exc

    db.refresh(event)
    return build_event_response(db, event)


def list_events(db: Session) -> list[EventResponse]:
    events = db.scalars(select(Event).order_by(Event.date, Event.start_time)).all()
    return [build_event_response(db, event) for event in events]


def get_event(db: Session, event_id: UUID) -> EventResponse:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    return build_event_response(db, event)


def update_event(db: Session, event_id: UUID, event_data: EventUpdate) -> EventResponse:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    update_data = event_data.model_dump(
        exclude_unset=True,
        exclude={"group_ids", "attendance_member_ids"},
    )
    for field, value in update_data.items():
        setattr(event, field, value)

    if event_data.group_ids is not None:
        sync_event_groups(db, event.id, event_data.group_ids)

    if event_data.attendance_member_ids is not None:
        sync_event_attendances(db, event.id, event_data.attendance_member_ids)

    db.commit()
    db.refresh(event)
    return build_event_response(db, event)


def list_event_attendances(db: Session, event_id: UUID) -> list[AttendanceResponse]:
    if not db.get(Event, event_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    return db.scalars(
        select(Attendance)
        .where(Attendance.event_id == event_id)
        .order_by(Attendance.checked_in_at.desc())
    ).all()


def create_event_attendance(
    db: Session,
    event_id: UUID,
    attendance_data: EventAttendanceCreate,
) -> AttendanceResponse:
    if not db.get(Event, event_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    if not db.get(Member, attendance_data.member_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    attendance = Attendance(
        event_id=event_id,
        member_id=attendance_data.member_id,
        note=attendance_data.note,
    )
    db.add(attendance)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already exists for this member and event.",
        ) from exc

    db.refresh(attendance)
    return attendance


def delete_event_attendance(db: Session, event_id: UUID, member_id: UUID) -> None:
    attendance = db.scalar(
        select(Attendance).where(
            Attendance.event_id == event_id,
            Attendance.member_id == member_id,
        )
    )
    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance not found.")

    db.delete(attendance)
    db.commit()


def delete_event(db: Session, event_id: UUID) -> None:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    db.delete(event)
    db.commit()
