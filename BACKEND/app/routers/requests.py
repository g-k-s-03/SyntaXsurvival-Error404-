from datetime import date, datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.audit import write_audit_log
from app.database import get_db
from app.deps import get_current_user
from app.models.donor_profile import DonorProfile
from app.models.request import BloodRequest, RequestStatus
from app.models.request_alert import AlertStatus, RequestAlert
from app.models.request_match import MatchStatus, RequestMatch
from app.models.user import User, UserRole
from app.schemas.request import (
    AlertActionResponse,
    MatchPublic,
    RequestCreate,
    RequestCreateResponse,
    RequestPublic,
)
from app.utils.geofence import estimate_distance_km, is_within_geofence

router = APIRouter(prefix="/requests", tags=["requests"])
FIRST_WAVE_SIZE = 5
settings = get_settings()
COMPATIBILITY_MATRIX: dict[str, dict[str, float]] = {
    "O-": {"O-": 1.0},
    "O+": {"O+": 1.0, "O-": 0.95},
    "A-": {"A-": 1.0, "O-": 0.95},
    "A+": {"A+": 1.0, "A-": 0.95, "O+": 0.9, "O-": 0.85},
    "B-": {"B-": 1.0, "O-": 0.95},
    "B+": {"B+": 1.0, "B-": 0.95, "O+": 0.9, "O-": 0.85},
    "AB-": {"AB-": 1.0, "A-": 0.92, "B-": 0.92, "O-": 0.88},
    "AB+": {
        "AB+": 1.0,
        "AB-": 0.96,
        "A+": 0.94,
        "A-": 0.92,
        "B+": 0.94,
        "B-": 0.92,
        "O+": 0.9,
        "O-": 0.88,
    },
}


def _is_donor_eligible(profile: DonorProfile) -> bool:
    if not profile.consent_share:
        return False
    if not profile.is_available:
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
        .options(
            selectinload(BloodRequest.alerts),
            selectinload(BloodRequest.matches),
        )
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
    response_model=RequestCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_request(
    body: RequestCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RequestCreateResponse:
    _require_hospital(user)
    geofence_km = body.geofence_km or settings.default_geofence_km

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

    candidate_bloods = set(
        COMPATIBILITY_MATRIX.get(body.blood_group, {}).keys()
    )
    candidates = db.query(DonorProfile).filter(
        DonorProfile.blood_group.in_(candidate_bloods)
    ).all()
    eligible = [
        p
        for p in candidates
        if _is_donor_eligible(p)
        and is_within_geofence(
            center_location=body.location_text,
            target_location=p.area_text,
            radius_km=geofence_km,
        )
    ]

    ranked_rows: list[RequestMatch] = []
    if eligible:
        scored: list[tuple[DonorProfile, float, float, float | None]] = []
        for profile in eligible:
            comp = COMPATIBILITY_MATRIX.get(body.blood_group, {}).get(
                profile.blood_group, 0.0
            )
            if comp <= 0:
                continue
            dist = estimate_distance_km(body.location_text, profile.area_text)
            distance_penalty = (dist * 2.0) if dist is not None else 20.0
            final = (comp * 100.0) - distance_penalty
            scored.append((profile, comp * 100.0, final, dist))

        scored.sort(
            key=lambda row: (
                -row[2],
                row[3] if row[3] is not None else float("inf"),
            )
        )

        req.status = RequestStatus.matched
        req.matched_at = now
        for idx, (profile, comp_score, final_score, dist) in enumerate(
            scored, start=1
        ):
            match = RequestMatch(
                request_id=req.id,
                donor_user_id=profile.user_id,
                rank=idx,
                compatibility_score=round(comp_score, 2),
                distance_km=round(dist, 2) if dist is not None else None,
                final_score=round(final_score, 2),
                status=MatchStatus.queued,
            )
            db.add(match)
            ranked_rows.append(match)

        for match in ranked_rows[:FIRST_WAVE_SIZE]:
            db.add(
                RequestAlert(
                    request_id=req.id,
                    donor_user_id=match.donor_user_id,
                    status=AlertStatus.alerted,
                )
            )
            match.status = MatchStatus.alerted
        req.status = RequestStatus.alerted
        req.alerted_at = now

    db.commit()
    req = _get_request_or_404(db, req.id)
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="request.create",
        target_type="request",
        target_id=str(req.id),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        meta={"blood_group": req.blood_group, "urgency": req.urgency.value, "units": req.units},
    )
    first_wave = ranked_rows[:FIRST_WAVE_SIZE]
    return RequestCreateResponse(
        request=RequestPublic.model_validate(req),
        first_wave=[MatchPublic.model_validate(m) for m in first_wave],
    )


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
    request: Request,
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
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="request.cancel",
        target_type="request",
        target_id=str(req.id),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return RequestPublic.model_validate(req)


@router.post("/{request_id}/fulfill", response_model=RequestPublic)
def fulfill_request(
    request_id: uuid.UUID,
    request: Request,
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
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="request.fulfill",
        target_type="request",
        target_id=str(req.id),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return RequestPublic.model_validate(req)


@router.post("/{request_id}/accept", response_model=AlertActionResponse)
def accept_alert(
    request_id: uuid.UUID,
    request: Request,
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
    selected_match = (
        db.query(RequestMatch)
        .filter(
            RequestMatch.request_id == req.id,
            RequestMatch.donor_user_id == user.id,
        )
        .first()
    )
    if selected_match:
        selected_match.status = MatchStatus.accepted

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
    db.query(RequestMatch).filter(
        RequestMatch.request_id == req.id,
        RequestMatch.donor_user_id != user.id,
        RequestMatch.status == MatchStatus.alerted,
    ).update({"status": MatchStatus.declined}, synchronize_session=False)

    db.commit()
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="request.alert.accept",
        target_type="request",
        target_id=str(req.id),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return AlertActionResponse(status="accepted", request_status=req.status)


@router.post("/{request_id}/decline", response_model=AlertActionResponse)
def decline_alert(
    request_id: uuid.UUID,
    request: Request,
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
    row = (
        db.query(RequestMatch)
        .filter(
            RequestMatch.request_id == req.id,
            RequestMatch.donor_user_id == user.id,
        )
        .first()
    )
    if row and row.status in {MatchStatus.queued, MatchStatus.alerted}:
        row.status = MatchStatus.declined
    db.commit()
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="request.alert.decline",
        target_type="request",
        target_id=str(req.id),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return AlertActionResponse(status="declined", request_status=req.status)
