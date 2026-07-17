from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.event import Event
from app.models.member import Member
from app.schemas.attendance import AttendanceCreate, AttendanceResponse, AttendanceUpdate


def create_attendance(db: Session, attendance_data: AttendanceCreate) -> AttendanceResponse:
    if not db.get(Event, attendance_data.event_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    if not db.get(Member, attendance_data.member_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    attendance = Attendance(**attendance_data.model_dump())
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


def list_attendances(db: Session) -> list[AttendanceResponse]:
    return db.scalars(select(Attendance).order_by(Attendance.checked_in_at.desc())).all()


def get_attendance(db: Session, attendance_id: UUID) -> AttendanceResponse:
    attendance = db.get(Attendance, attendance_id)
    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance not found.")

    return attendance


def update_attendance(
    db: Session,
    attendance_id: UUID,
    attendance_data: AttendanceUpdate,
) -> AttendanceResponse:
    attendance = db.get(Attendance, attendance_id)
    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance not found.")

    for field, value in attendance_data.model_dump(exclude_unset=True).items():
        setattr(attendance, field, value)

    db.commit()
    db.refresh(attendance)
    return attendance


def delete_attendance(db: Session, attendance_id: UUID) -> None:
    attendance = db.get(Attendance, attendance_id)
    if not attendance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance not found.")

    db.delete(attendance)
    db.commit()
