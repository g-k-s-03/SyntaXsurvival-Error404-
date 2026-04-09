from pydantic import BaseModel, Field

from app.models.user import UserRole
from app.schemas.user import UserPublic


class OtpSendRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)


class OtpSendResponse(BaseModel):
    ok: bool = True
    expires_in_seconds: int = 600
    demo_otp: str | None = None


class OtpVerifyRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    code: str = Field(..., min_length=6, max_length=6)
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
