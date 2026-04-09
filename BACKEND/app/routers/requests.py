from datetime import date, datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.donor_profile import DonorProfile
from app.models.request import BloodRequest, RequestStatus
from app.models.request_alert import AlertStatus, RequestAlert
from app.models.user import User, UserRole
from app.schemas.request import (
    AlertActionResponse,
    RequestCreate,
    RequestPublic,
)

router = APIRouter(prefix="/requests", tags=["requests"])


def _is_donor_eligible(profile: DonorProfile) -> bool:
    if not profile.consent_share:
        return False
    if profile.last_donation_date is None:
        return True
    return (date.today() - profile.last_donation_date).days >= 56


def _require_hospital(user: User) -> None:
    if user.role != UserRole.hospital:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hospital role required",
        )


def _require_donor(user: User) -> None:
    if user.role != UserRole.donor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Donor role required",
        )


def _get_request_or_404(db: Session, request_id: uuid.UUID) -> BloodRequest:
    req = (
        db.query(BloodRequest)
        .options(selectinload(BloodRequest.alerts))
        .filter(BloodRequest.id == request_id)
        .first()
    )
    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )
    return req


@router.post(
    "",
    response_model=RequestPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_request(
    body: RequestCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RequestPublic:
    _require_hospital(user)

    now = datetime.now(timezone.utc)
    req = BloodRequest(
        hospital_user_id=user.id,
        blood_group=body.blood_group,
        units=body.units,
        urgency=body.urgency,
        location_text=body.location_text.strip(),
        notes=body.notes.strip() if body.notes else None,
        status=RequestStatus.submitted,
    )
    db.add(req)
    db.flush()

    candidates = (
        db.query(DonorProfile)
        .filter(DonorProfile.blood_group == body.blood_group)
        .filter(DonorProfile.consent_share.is_(True))
        .all()
    )
    eligible = [p for p in candidates if _is_donor_eligible(p)]

    if eligible:
        req.status = RequestStatus.matched
        req.matched_at = now
        for profile in eligible[:10]:
            db.add(
                RequestAlert(
                    request_id=req.id,
                    donor_user_id=profile.user_id,
                    status=AlertStatus.alerted,
                )
            )
        req.status = RequestStatus.alerted
        req.alerted_at = now

    db.commit()
    db.refresh(req)
    return RequestPublic.model_validate(req)


@router.get("/{request_id}", response_model=RequestPublic)
def view_request(
    request_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RequestPublic:
    req = _get_request_or_404(db, request_id)
    if user.role == UserRole.hospital and req.hospital_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your request",
        )
    if user.role == UserRole.donor:
        has_alert = any(a.donor_user_id == user.id for a in req.alerts)
        if not has_alert:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this request",
            )
    return RequestPublic.model_validate(req)


@router.post("/{request_id}/cancel", response_model=RequestPublic)
def cancel_request(
    request_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RequestPublic:
    _require_hospital(user)
    req = _get_request_or_404(db, request_id)
    if req.hospital_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your request",
        )
    if req.status not in {
        RequestStatus.submitted,
        RequestStatus.matched,
        RequestStatus.alerted,
        RequestStatus.accepted,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel request in state {req.status.value}",
        )
    req.status = RequestStatus.cancelled
    req.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)
    return RequestPublic.model_validate(req)


@router.post("/{request_id}/fulfill", response_model=RequestPublic)
def fulfill_request(
    request_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RequestPublic:
    _require_hospital(user)
    req = _get_request_or_404(db, request_id)
    if req.hospital_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your request",
        )
    if req.status != RequestStatus.accepted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only accepted requests can be fulfilled",
        )
    req.status = RequestStatus.fulfilled
    req.fulfilled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)
    return RequestPublic.model_validate(req)


@router.post("/{request_id}/accept", response_model=AlertActionResponse)
def accept_alert(
    request_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertActionResponse:
    _require_donor(user)
    req = _get_request_or_404(db, request_id)
    if req.status != RequestStatus.alerted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request is not accepting donor responses",
        )
    alert = (
        db.query(RequestAlert)
        .filter(
            RequestAlert.request_id == req.id,
            RequestAlert.donor_user_id == user.id,
        )
        .first()
    )
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No alert assigned to this donor",
        )
    if alert.status != AlertStatus.alerted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Alert already {alert.status.value}",
        )

    now = datetime.now(timezone.utc)
    alert.status = AlertStatus.accepted
    alert.responded_at = now
    req.status = RequestStatus.accepted
    req.accepted_donor_user_id = user.id
    req.accepted_at = now

    others = (
        db.query(RequestAlert)
        .filter(
            RequestAlert.request_id == req.id,
            RequestAlert.donor_user_id != user.id,
            RequestAlert.status == AlertStatus.alerted,
        )
        .all()
    )
    for row in others:
        row.status = AlertStatus.declined
        row.responded_at = now

    db.commit()
    return AlertActionResponse(status="accepted", request_status=req.status)


@router.post("/{request_id}/decline", response_model=AlertActionResponse)
def decline_alert(
    request_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AlertActionResponse:
    _require_donor(user)
    req = _get_request_or_404(db, request_id)
    if req.status != RequestStatus.alerted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request is not accepting donor responses",
        )
    alert = (
        db.query(RequestAlert)
        .filter(
            RequestAlert.request_id == req.id,
            RequestAlert.donor_user_id == user.id,
        )
        .first()
    )
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No alert assigned to this donor",
        )
    if alert.status != AlertStatus.alerted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Alert already {alert.status.value}",
        )
    alert.status = AlertStatus.declined
    alert.responded_at = datetime.now(timezone.utc)
    db.commit()
    return AlertActionResponse(status="declined", request_status=req.status)
