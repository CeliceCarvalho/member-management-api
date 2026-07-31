from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.group import Group
from app.models.group_participation import GroupParticipation
from app.models.member import Member
from app.schemas.group import GroupCreate, GroupResponse, GroupUpdate


def validate_group_leaders(db: Session, leader_id: UUID | None, co_leader_id: UUID | None) -> None:
    if leader_id and co_leader_id and leader_id == co_leader_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leader and co-leader must be different members.",
        )

    for member_id, label in ((leader_id, "Leader"), (co_leader_id, "Co-leader")):
        if member_id and not db.get(Member, member_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{label} member not found.",
            )


def get_active_member_ids(db: Session, group_id: UUID) -> list[UUID]:
    return db.scalars(
        select(GroupParticipation.member_id).where(
            GroupParticipation.group_id == group_id,
            GroupParticipation.active.is_(True),
        )
    ).all()


def build_group_response(db: Session, group: Group) -> GroupResponse:
    return GroupResponse.model_validate(group).model_copy(
        update={"member_ids": get_active_member_ids(db, group.id)}
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


def sync_group_members(db: Session, group_id: UUID, member_ids: list[UUID]) -> None:
    validate_member_ids(db, member_ids)

    target_member_ids = set(member_ids)
    participations = db.scalars(
        select(GroupParticipation).where(GroupParticipation.group_id == group_id)
    ).all()

    participation_by_member_id = {
        participation.member_id: participation
        for participation in participations
        if participation.active
    }

    for participation in participation_by_member_id.values():
        if participation.member_id not in target_member_ids:
            participation.active = False
            participation.left_at = datetime.utcnow()

    active_member_ids = set(participation_by_member_id.keys())
    for member_id in target_member_ids - active_member_ids:
        db.add(GroupParticipation(member_id=member_id, group_id=group_id))


def create_group(db: Session, group_data: GroupCreate) -> GroupResponse:
    validate_group_leaders(db, group_data.leader_id, group_data.co_leader_id)

    create_data = group_data.model_dump(exclude={"member_ids"})
    group = Group(**create_data)
    db.add(group)

    try:
        db.flush()
        sync_group_members(db, group.id, group_data.member_ids)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Group with this name already exists.",
        ) from exc

    db.refresh(group)
    return build_group_response(db, group)


def list_groups(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 50,
    search: str | None = None,
    type_filter: str | None = None,
    active: bool | None = None,
) -> tuple[list[GroupResponse], int]:
    query = select(Group)
    count_query = select(func.count()).select_from(Group)

    filters = []
    if search:
        filters.append(Group.name.ilike(f"%{search.strip()}%"))
    if type_filter:
        filters.append(Group.type == type_filter)
    if active is not None:
        filters.append(Group.active.is_(active))

    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    total = db.scalar(count_query) or 0
    groups = db.scalars(
        query.order_by(Group.name).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return [build_group_response(db, group) for group in groups], total


def get_group(db: Session, group_id: UUID) -> GroupResponse:
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

    return build_group_response(db, group)


def update_group(db: Session, group_id: UUID, group_data: GroupUpdate) -> GroupResponse:
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

    update_data = group_data.model_dump(exclude_unset=True, exclude={"member_ids"})
    leader_id = update_data.get("leader_id", group.leader_id)
    co_leader_id = update_data.get("co_leader_id", group.co_leader_id)
    validate_group_leaders(db, leader_id, co_leader_id)

    for field, value in update_data.items():
        setattr(group, field, value)

    try:
        if group_data.member_ids is not None:
            sync_group_members(db, group.id, group_data.member_ids)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Group with this name already exists.",
        ) from exc

    db.refresh(group)
    return build_group_response(db, group)


def delete_group(db: Session, group_id: UUID) -> None:
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found.")

    db.delete(group)
    db.commit()
