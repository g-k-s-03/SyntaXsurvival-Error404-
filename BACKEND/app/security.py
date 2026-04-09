import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.otp_challenge import OtpChallenge
from app.models.user import User, UserRole


def normalize_phone(raw: str) -> str:
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) >= 10:
        return digits[-10:]
    return digits


def hash_otp(settings: Settings, phone: str, code: str) -> str:
    msg = f"{phone}:{code}".encode()
    return hmac.new(settings.secret_key.encode(), msg, hashlib.sha256).hexdigest()


def issue_otp_challenge(db: Session, settings: Settings, phone: str) -> str:
    if settings.demo_mode:
        code = settings.demo_otp_code
    else:
        code = f"{secrets.randbelow(1_000_000):06d}"

    db.query(OtpChallenge).filter(OtpChallenge.phone == phone).delete()
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    row = OtpChallenge(phone=phone, code_hash=hash_otp(settings, phone, code), expires_at=expires)
    db.add(row)
    db.commit()
    return code


def verify_otp(db: Session, settings: Settings, phone: str, code: str) -> bool:
    now = datetime.now(timezone.utc)
    row = (
        db.query(OtpChallenge)
        .filter(OtpChallenge.phone == phone, OtpChallenge.expires_at > now)
        .order_by(OtpChallenge.created_at.desc())
        .first()
    )
    if not row:
        return False
    expected = hash_otp(settings, phone, code)
    if not hmac.compare_digest(row.code_hash, expected):
        return False
    db.query(OtpChallenge).filter(OtpChallenge.phone == phone).delete()
    db.commit()
    return True


def create_access_token(settings: Settings, user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user.id),
        "phone": user.phone,
        "role": user.role.value,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(settings: Settings, token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def get_user_from_token(db: Session, settings: Settings, token: str) -> User | None:
    try:
        payload = decode_token(settings, token)
        sub = payload.get("sub")
        if not sub:
            return None
        return db.query(User).filter(User.id == uuid.UUID(str(sub))).first()
    except (JWTError, ValueError):
        return None


def get_or_create_user(db: Session, phone: str, role: UserRole) -> User:
    user = db.query(User).filter(User.phone == phone).first()
    if user:
        if user.role != role:
            raise ValueError("Role mismatch for existing account")
        user.phone_verified = True
        db.commit()
        db.refresh(user)
        return user
    user = User(phone=phone, role=role, phone_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
