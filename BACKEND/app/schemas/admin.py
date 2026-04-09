from __future__ import annotations

from datetime import date
import uuid

from pydantic import BaseModel, Field


class AdminOverview(BaseModel):
    total_donors: int
    available_now: int
    active_requests: int
    fulfilled_today: int


class AdminDonorRow(BaseModel):
    user_id: uuid.UUID
    full_name: str
    blood_group: str
    area_text: str
    status: str = Field(..., description="available|locked|offline")
    last_donation_date: date | None = None


class BroadcastRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    target: str = Field(..., max_length=120)


class BroadcastResponse(BaseModel):
    recipients: int
    target: str

