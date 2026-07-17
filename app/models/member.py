import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MemberCategory(str, enum.Enum):
    PASTOR = "PASTOR"
    MEMBER = "MEMBER"
    VISITOR = "VISITOR"
    DEACON = "DEACON"
    CONGREGANT = "CONGREGANT"


class MemberStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    tax_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), unique=True, nullable=True, index=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[MemberCategory] = mapped_column(Enum(MemberCategory), nullable=False)
    status: Mapped[MemberStatus] = mapped_column(Enum(MemberStatus), default=MemberStatus.ACTIVE, nullable=False)
    registration_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
