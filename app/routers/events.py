from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.attendance import AttendanceResponse, EventAttendanceCreate
from app.schemas.event import EventCreate, EventResponse, EventUpdate
from app.services import events as event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event_data: EventCreate, db: Session = Depends(get_db)):
    return event_service.create_event(db, event_data)


@router.get("/", response_model=list[EventResponse])
def list_events(db: Session = Depends(get_db)):
    return event_service.list_events(db)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: UUID, db: Session = Depends(get_db)):
    return event_service.get_event(db, event_id)


@router.patch("/{event_id}", response_model=EventResponse)
def update_event(event_id: UUID, event_data: EventUpdate, db: Session = Depends(get_db)):
    return event_service.update_event(db, event_id, event_data)


@router.get("/{event_id}/attendances", response_model=list[AttendanceResponse])
def list_event_attendances(event_id: UUID, db: Session = Depends(get_db)):
    return event_service.list_event_attendances(db, event_id)


@router.post(
    "/{event_id}/attendances",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event_attendance(
    event_id: UUID,
    attendance_data: EventAttendanceCreate,
    db: Session = Depends(get_db),
):
    return event_service.create_event_attendance(db, event_id, attendance_data)


@router.delete("/{event_id}/attendances/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_attendance(event_id: UUID, member_id: UUID, db: Session = Depends(get_db)):
    event_service.delete_event_attendance(db, event_id, member_id)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: UUID, db: Session = Depends(get_db)):
    event_service.delete_event(db, event_id)
