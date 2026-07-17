import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import ARRAY, Boolean, Date, DateTime, Enum, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EventStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    PENDING_REGISTRATION = "PENDING_REGISTRATION"


class Weekday(str, enum.Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weekdays: Mapped[list[Weekday]] = mapped_column(ARRAY(Enum(Weekday)), default=list, nullable=False)
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus),
        default=EventStatus.SCHEDULED,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
