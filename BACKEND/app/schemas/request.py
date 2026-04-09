from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.request import RequestStatus, RequestUrgency
from app.models.request_alert import AlertStatus

VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


class RequestCreate(BaseModel):
    blood_group: str = Field(..., max_length=5)
    units: int = Field(..., ge=1, le=10)
    urgency: RequestUrgency
    location_text: str = Field(..., min_length=2, max_length=300)
    notes: str | None = Field(None, max_length=500)

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, value: str) -> str:
        normalized = value.strip().upper().replace("−", "-")
        if normalized not in VALID_BLOOD_GROUPS:
            raise ValueError("Invalid blood group")
        return normalized


class AlertActionResponse(BaseModel):
    status: str
    request_status: RequestStatus


class AlertPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    donor_user_id: uuid.UUID
    status: AlertStatus
    created_at: datetime
    responded_at: datetime | None = None


class RequestPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hospital_user_id: uuid.UUID
    blood_group: str
    units: int
    urgency: RequestUrgency
    location_text: str
    notes: str | None = None
    status: RequestStatus
    accepted_donor_user_id: uuid.UUID | None = None
    created_at: datetime
    matched_at: datetime | None = None
    alerted_at: datetime | None = None
    accepted_at: datetime | None = None
    fulfilled_at: datetime | None = None
    cancelled_at: datetime | None = None
    alerts: list[AlertPublic] = []
