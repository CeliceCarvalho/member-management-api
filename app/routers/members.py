from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.event import EventResponse
from app.schemas.member import MemberCreate, MemberResponse, MemberUpdate
from app.services import members as member_service

router = APIRouter(prefix="/members", tags=["members"])


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def create_member(member_data: MemberCreate, db: Session = Depends(get_db)):
    return member_service.create_member(db, member_data)


@router.get("/", response_model=list[MemberResponse])
def list_members(db: Session = Depends(get_db)):
    return member_service.list_members(db)


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: UUID, db: Session = Depends(get_db)):
    return member_service.get_member(db, member_id)


@router.get("/{member_id}/events", response_model=list[EventResponse])
def list_member_attended_events(member_id: UUID, db: Session = Depends(get_db)):
    return member_service.list_member_attended_events(db, member_id)


@router.patch("/{member_id}", response_model=MemberResponse)
def update_member(member_id: UUID, member_data: MemberUpdate, db: Session = Depends(get_db)):
    return member_service.update_member(db, member_id, member_data)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: UUID, db: Session = Depends(get_db)):
    member_service.delete_member(db, member_id)
