from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.group import GroupCreate, GroupResponse, GroupUpdate
from app.services import groups as group_service

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(group_data: GroupCreate, db: Session = Depends(get_db)):
    return group_service.create_group(db, group_data)


@router.get("/", response_model=list[GroupResponse])
def list_groups(db: Session = Depends(get_db)):
    return group_service.list_groups(db)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: UUID, db: Session = Depends(get_db)):
    return group_service.get_group(db, group_id)


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(group_id: UUID, group_data: GroupUpdate, db: Session = Depends(get_db)):
    return group_service.update_group(db, group_id, group_data)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: UUID, db: Session = Depends(get_db)):
    group_service.delete_group(db, group_id)
