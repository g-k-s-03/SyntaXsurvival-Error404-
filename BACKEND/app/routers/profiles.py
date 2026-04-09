from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.donor_profile import DonorProfile
from app.models.hospital_profile import HospitalProfile
from app.models.user import User, UserRole
from app.schemas.profile import DonorProfileCreate, HospitalProfileCreate
from app.security import normalize_phone

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/donor", status_code=status.HTTP_200_OK)
def upsert_donor_profile(
    body: DonorProfileCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if user.role != UserRole.donor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only donor accounts can save a donor profile",
        )
    ep = normalize_phone(body.emergency_phone)
    if len(ep) != 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emergency phone must be 10 digits",
        )
    row = db.query(DonorProfile).filter(DonorProfile.user_id == user.id).first()
    data = body.model_dump()
    data["emergency_phone"] = ep
    if row is None:
        row = DonorProfile(user_id=user.id, **data)
        db.add(row)
    else:
        for k, v in data.items():
            setattr(row, k, v)
    db.commit()
    return {"status": "saved"}


@router.post("/hospital", status_code=status.HTTP_200_OK)
def upsert_hospital_profile(
    body: HospitalProfileCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if user.role != UserRole.hospital:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospital accounts can save a hospital profile",
        )
    row = db.query(HospitalProfile).filter(HospitalProfile.user_id == user.id).first()
    data = body.model_dump()
    if row is None:
        row = HospitalProfile(user_id=user.id, verified=False, **data)
        db.add(row)
    else:
        for k, v in data.items():
            setattr(row, k, v)
    db.commit()
    return {"status": "saved"}
