from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.donor_profile import DonorProfile
from app.models.hospital_profile import HospitalProfile
from app.models.user import User
from app.schemas.profile import DonorPublic, HospitalPublic

router = APIRouter(tags=["directory"])


@router.get("/donors", response_model=list[DonorPublic])
def list_donors(
    db: Session = Depends(get_db),
    blood_group: str | None = Query(None, max_length=5),
) -> list[DonorPublic]:
    q = (
        db.query(DonorProfile)
        .join(User)
        .filter(DonorProfile.consent_share.is_(True))
        .filter(User.phone_verified.is_(True))
    )
    if blood_group:
        q = q.filter(DonorProfile.blood_group == blood_group)
    rows = q.all()
    return [DonorPublic.model_validate(r) for r in rows]


@router.get("/hospitals", response_model=list[HospitalPublic])
def list_hospitals(db: Session = Depends(get_db)) -> list[HospitalPublic]:
    rows = db.query(HospitalProfile).all()
    return [HospitalPublic.model_validate(r) for r in rows]
