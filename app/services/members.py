from datetime import date, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.event import Event
from app.models.group import Group
from app.models.group_participation import GroupParticipation
from app.models.member import Member
from app.schemas.event import EventResponse
from app.schemas.member import MemberCreate, MemberPresence, MemberResponse, MemberUpdate
from app.services.events import build_event_response


def calculate_age(birth_date: date) -> int:
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def get_active_group_ids(db: Session, member_id: UUID) -> list[UUID]:
    return db.scalars(
        select(GroupParticipation.group_id).where(
            GroupParticipation.member_id == member_id,
            GroupParticipation.active.is_(True),
        )
    ).all()


def calculate_member_attendance_rate(db: Session, member_id: UUID) -> float:
    total_events = db.scalar(select(func.count()).select_from(Event)) or 0
    if not total_events:
        return 0

    total_present = db.scalar(
        select(func.count(func.distinct(Attendance.event_id))).where(
            Attendance.member_id == member_id,
        )
    ) or 0

    return round(total_present / total_events * 100, 2)


def build_member_response(db: Session, member: Member) -> MemberResponse:
    attendance_rate = calculate_member_attendance_rate(db, member.id)
    presence = (
        MemberPresence.FREQUENT
        if attendance_rate >= 70
        else MemberPresence.ABSENT
    )

    return MemberResponse.model_validate(member).model_copy(
        update={
            "group_ids": get_active_group_ids(db, member.id),
            "presence": presence,
            "attendance_rate": attendance_rate,
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


def sync_member_groups(db: Session, member_id: UUID, group_ids: list[UUID]) -> None:
    validate_group_ids(db, group_ids)

    target_group_ids = set(group_ids)
    participations = db.scalars(
        select(GroupParticipation).where(GroupParticipation.member_id == member_id)
    ).all()

    participation_by_group_id = {
        participation.group_id: participation
        for participation in participations
        if participation.active
    }

    for participation in participation_by_group_id.values():
        if participation.group_id not in target_group_ids:
            participation.active = False
            participation.left_at = datetime.utcnow()

    active_group_ids = set(participation_by_group_id.keys())
    for group_id in target_group_ids - active_group_ids:
        db.add(GroupParticipation(member_id=member_id, group_id=group_id))


def create_member(db: Session, member_data: MemberCreate) -> MemberResponse:
    create_data = member_data.model_dump(exclude={"group_ids"})
    member = Member(**create_data, age=calculate_age(member_data.birth_date))
    db.add(member)

    try:
        db.flush()
        sync_member_groups(db, member.id, member_data.group_ids)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member with this tax_id or email already exists.",
        ) from exc

    db.refresh(member)
    return build_member_response(db, member)


def list_members(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 50,
    search: str | None = None,
    category: str | None = None,
    group_id: UUID | None = None,
) -> tuple[list[MemberResponse], int]:
    query = select(Member)
    count_query = select(func.count()).select_from(Member)

    filters = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(Member.name.ilike(term), Member.email.ilike(term)))
    if category:
        filters.append(Member.category == category)
    if group_id:
        query = query.join(
            GroupParticipation,
            GroupParticipation.member_id == Member.id,
        )
        count_query = count_query.join(
            GroupParticipation,
            GroupParticipation.member_id == Member.id,
        )
        filters.extend(
            [
                GroupParticipation.group_id == group_id,
                GroupParticipation.active.is_(True),
            ]
        )

    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    total = db.scalar(count_query) or 0
    members = db.scalars(
        query.order_by(Member.name).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return [build_member_response(db, member) for member in members], total


def get_member(db: Session, member_id: UUID) -> MemberResponse:
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    return build_member_response(db, member)


def list_member_attended_events(db: Session, member_id: UUID) -> list[EventResponse]:
    if not db.get(Member, member_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    events = db.scalars(
        select(Event)
        .join(Attendance, Attendance.event_id == Event.id)
        .where(Attendance.member_id == member_id)
        .order_by(Event.date.desc(), Event.start_time.desc())
    ).all()
    return [build_event_response(db, event) for event in events]


def update_member(db: Session, member_id: UUID, member_data: MemberUpdate) -> MemberResponse:
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    update_data = member_data.model_dump(exclude_unset=True, exclude={"group_ids"})
    for field, value in update_data.items():
        setattr(member, field, value)

    if member_data.birth_date is not None:
        member.age = calculate_age(member_data.birth_date)

    try:
        if member_data.group_ids is not None:
            sync_member_groups(db, member.id, member_data.group_ids)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member with this tax_id or email already exists.",
        ) from exc

    db.refresh(member)
    return build_member_response(db, member)


def delete_member(db: Session, member_id: UUID) -> None:
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    db.delete(member)
    db.commit()
