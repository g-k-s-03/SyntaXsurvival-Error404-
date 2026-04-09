import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone: str
    role: UserRole
    phone_verified: bool


class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: UserPublic
    donor_profile: dict[str, Any] | None = None
    hospital_profile: dict[str, Any] | None = None
