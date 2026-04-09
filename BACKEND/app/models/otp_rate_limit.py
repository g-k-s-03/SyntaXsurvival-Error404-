from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OtpKeyType(str, enum.Enum):
    phone = "phone"
    ip = "ip"


class OtpRateLimit(Base):
    __tablename__ = "otp_rate_limits"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key_type: Mapped[OtpKeyType] = mapped_column(
        SAEnum(OtpKeyType, name="otp_key_type"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    send_window_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    send_count_in_window: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resend_available_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    fail_window_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    failed_verifies_in_window: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

