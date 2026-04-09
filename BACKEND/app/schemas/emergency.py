import uuid

from pydantic import BaseModel, Field, field_validator

from app.sanitization import sanitize_text


class EmergencyTriggerRequest(BaseModel):
    request_id: uuid.UUID
    is_emergency: bool
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    blood_group: str = Field(..., min_length=2, max_length=5)

    @field_validator("blood_group")
    @classmethod
    def normalize_blood_group(cls, value: str) -> str:
        return sanitize_text(value).upper().replace("−", "-")


class EmergencyTriggerResponse(BaseModel):
    started: bool
    radii: list[int]
