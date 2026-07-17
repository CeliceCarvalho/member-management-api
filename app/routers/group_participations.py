from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.group import Group
from app.models.group_participation import GroupParticipation
from app.models.member import Member
from app.schemas.group_participation import (
    GroupParticipationCreate,
    GroupParticipationResponse,
)

router = APIRouter(prefix="/group-participations", tags=["group participations"])


@router.post("/", response_model=GroupParticipationResponse, status_code=status.HTTP_201_CREATED)
def create_group_participation(
    participation_data: GroupParticipationCreate,
    db: Session = Depends(get_db),
):
    if not db.get(Member, participation_data.member_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    if not db.get(Group, participation_data.group_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

    active_participation = db.scalar(
        select(GroupParticipation).where(
            GroupParticipation.member_id == participation_data.member_id,
            GroupParticipation.group_id == participation_data.group_id,
            GroupParticipation.active.is_(True),
        )
    )
    if active_participation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member already has an active participation in this group.",
        )

    participation = GroupParticipation(**participation_data.model_dump())
    db.add(participation)
    db.commit()
    db.refresh(participation)
    return participation


@router.get("/", response_model=list[GroupParticipationResponse])
def list_group_participations(db: Session = Depends(get_db)):
    return db.scalars(
        select(GroupParticipation).order_by(GroupParticipation.joined_at.desc())
    ).all()


@router.get("/{participation_id}", response_model=GroupParticipationResponse)
def get_group_participation(participation_id: UUID, db: Session = Depends(get_db)):
    participation = db.get(GroupParticipation, participation_id)
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group participation not found.",
        )

    return participation


@router.patch("/{participation_id}/leave", response_model=GroupParticipationResponse)
def leave_group(participation_id: UUID, db: Session = Depends(get_db)):
    participation = db.get(GroupParticipation, participation_id)
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group participation not found.",
        )

    if not participation.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Group participation is already inactive.",
        )

    participation.active = False
    participation.left_at = datetime.utcnow()
    db.commit()
    db.refresh(participation)
    return participation


@router.delete("/{participation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_participation(participation_id: UUID, db: Session = Depends(get_db)):
    participation = db.get(GroupParticipation, participation_id)
    if not participation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group participation not found.",
        )

    db.delete(participation)
    db.commit()
