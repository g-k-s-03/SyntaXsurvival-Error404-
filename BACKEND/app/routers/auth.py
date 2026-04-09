from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.auth import OtpSendRequest, OtpSendResponse, OtpVerifyRequest, TokenResponse
from app.schemas.user import UserPublic
from app.security import (
    create_access_token,
    get_or_create_user,
    issue_otp_challenge,
    normalize_phone,
    verify_otp,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/otp/send", response_model=OtpSendResponse)
def send_otp(body: OtpSendRequest, db: Session = Depends(get_db)) -> OtpSendResponse:
    settings = get_settings()
    phone = normalize_phone(body.phone)
    if len(phone) != 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone must be 10 digits (India)")
    code = issue_otp_challenge(db, settings, phone)
    return OtpSendResponse(
        demo_otp=code if settings.demo_mode else None,
    )


@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp_route(body: OtpVerifyRequest, db: Session = Depends(get_db)) -> TokenResponse:
    settings = get_settings()
    phone = normalize_phone(body.phone)
    if len(phone) != 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone must be 10 digits (India)")
    if not verify_otp(db, settings, phone, body.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    user = get_or_create_user(db, phone, body.role)
    token = create_access_token(settings, user)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))
