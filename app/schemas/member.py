from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.member import MemberCategory, MemberStatus


class MemberPresence(str, Enum):
    FREQUENT = "FREQUENT"
    ABSENT = "ABSENT"


class MemberBase(BaseModel):
    name: str
    tax_id: str
    birth_date: date
    phone: str | None = None
    email: EmailStr | None = None
    photo_url: str | None = None
    category: MemberCategory


class MemberCreate(MemberBase):
    group_ids: list[UUID] = Field(default_factory=list)


class MemberUpdate(BaseModel):
    name: str | None = None
    tax_id: str | None = None
    birth_date: date | None = None
    phone: str | None = None
    email: EmailStr | None = None
    photo_url: str | None = None
    category: MemberCategory | None = None
    status: MemberStatus | None = None
    group_ids: list[UUID] | None = None


class MemberResponse(MemberBase):
    id: UUID
    age: int
    status: MemberStatus
    presence: MemberPresence = MemberPresence.ABSENT
    attendance_rate: float = 0
    registration_date: datetime
    group_ids: list[UUID] = Field(default_factory=list)

    model_config = {"from_attributes": True}
