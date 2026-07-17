from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.attendance import AttendanceCreate, AttendanceResponse, AttendanceUpdate
from app.services import attendances as attendance_service

router = APIRouter(prefix="/attendances", tags=["attendances"])


@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def create_attendance(attendance_data: AttendanceCreate, db: Session = Depends(get_db)):
    return attendance_service.create_attendance(db, attendance_data)


@router.get("/", response_model=list[AttendanceResponse])
def list_attendances(db: Session = Depends(get_db)):
    return attendance_service.list_attendances(db)


@router.get("/{attendance_id}", response_model=AttendanceResponse)
def get_attendance(attendance_id: UUID, db: Session = Depends(get_db)):
    return attendance_service.get_attendance(db, attendance_id)


@router.patch("/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(
    attendance_id: UUID,
    attendance_data: AttendanceUpdate,
    db: Session = Depends(get_db),
):
    return attendance_service.update_attendance(db, attendance_id, attendance_data)


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(attendance_id: UUID, db: Session = Depends(get_db)):
    attendance_service.delete_attendance(db, attendance_id)
