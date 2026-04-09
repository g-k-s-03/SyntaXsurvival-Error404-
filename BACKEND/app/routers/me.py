from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserMe, UserPublic

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserMe)
def read_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserMe:
    _ = db
    donor = user.donor_profile
    hospital = user.hospital_profile
    return UserMe(
        user=UserPublic.model_validate(user),
        donor_profile=_profile_dict(donor),
        hospital_profile=_profile_dict(hospital),
    )


def _profile_dict(obj: object | None) -> dict | None:
    if obj is None:
        return None
    cols = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}  # type: ignore[attr-defined]
    out: dict = {}
    for k, v in cols.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserMe, UserPublic

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserMe)
def read_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserMe:
    _ = db
    donor = user.donor_profile
    hospital = user.hospital_profile
    return UserMe(
        user=UserPublic.model_validate(user),
        donor_profile=_profile_dict(donor),
        hospital_profile=_profile_dict(hospital),
    )


def _profile_dict(obj: object | None) -> dict | None:
    if obj is None:
        return None
    cols = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}  # type: ignore[attr-defined]
    out: dict = {}
    for k, v in cols.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out
