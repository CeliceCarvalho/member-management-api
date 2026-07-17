import enum
import uuid
from datetime import time

from sqlalchemy import Boolean, Enum, ForeignKey, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GroupType(str, enum.Enum):
    CELL = "CELL"
    MINISTRY = "MINISTRY"
    DEPARTMENT = "DEPARTMENT"
    EBD_CLASS = "EBD_CLASS"


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    type: Mapped[GroupType] = mapped_column(Enum(GroupType), nullable=False)
    weekday: Mapped[str | None] = mapped_column(String(20), nullable=True)
    time: Mapped[time | None] = mapped_column(Time, nullable=True)
    recurring_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    leader_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
    )
    co_leader_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
