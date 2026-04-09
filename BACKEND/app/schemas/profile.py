from datetime import date
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


class DonorProfileCreate(BaseModel):
    full_name: str = Field(..., max_length=200)
    age: int = Field(..., ge=18, le=65)
    weight_kg: int = Field(..., ge=50)
    area_text: str = Field(..., max_length=300)
    blood_group: str = Field(..., max_length=5)
    last_donation_date: date | None = None
    medical_notes: str | None = None
    aadhaar_last4: str = Field(..., min_length=4, max_length=4)
    emergency_phone: str = Field(..., max_length=15)
    consent_share: bool = False

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, value: str) -> str:
        normalized = value.strip().upper().replace("−", "-")
        if normalized not in VALID_BLOOD_GROUPS:
            raise ValueError(
                "Blood group must be one of A+, A-, B+, B-, AB+, AB-, O+, O-"
            )
        return normalized

    @field_validator("aadhaar_last4")
    @classmethod
    def validate_aadhaar_last4(cls, value: str) -> str:
        if not value.isdigit() or len(value) != 4:
            raise ValueError("Aadhaar last4 must be exactly 4 digits")
        return value


class DonorPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    area_text: str
    blood_group: str
    age: int
    consent_share: bool


class HospitalProfileCreate(BaseModel):
    facility_name: str = Field(..., max_length=300)
    contact_person: str = Field(..., max_length=200)
    designation: str | None = Field(None, max_length=200)
    facility_type: str | None = Field(None, max_length=120)
    address: str = Field(..., max_length=500)
    city: str = Field(..., max_length=120)
    area: str | None = Field(None, max_length=200)
    gps_text: str | None = Field(None, max_length=200)
    consent: bool = False


class HospitalPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    facility_name: str
    city: str
    area: str | None
    facility_type: str | None
    verified: bool
