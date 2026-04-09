from __future__ import annotations

from datetime import date, datetime, time, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.audit import write_audit_log
from app.database import get_db
from app.deps import get_current_user
from app.models.donor_profile import DonorProfile
from app.models.request import BloodRequest, RequestStatus
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminDonorRow,
    AdminOverview,
    BroadcastRequest,
    BroadcastResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(user: User) -> None:
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required"
        )


@router.get("/overview", response_model=AdminOverview)
def overview(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdminOverview:
    _require_admin(user)
    total_donors = db.query(DonorProfile).count()
    today = date.today()
    candidates = (
        db.query(DonorProfile)
        .filter(DonorProfile.consent_share.is_(True))
        .filter(DonorProfile.is_available.is_(True))
        .all()
    )
    available_now = sum(
        1
        for r in candidates
        if r.last_donation_date is None or (today - r.last_donation_date).days >= 56
    )
    active_requests = (
        db.query(BloodRequest)
        .filter(
            BloodRequest.status.in_(
                [
                    RequestStatus.submitted,
                    RequestStatus.matched,
                    RequestStatus.alerted,
                    RequestStatus.accepted,
                ]
            )
        )
        .count()
    )
    start = datetime.combine(today, time.min).replace(tzinfo=timezone.utc)
    fulfilled_today = (
        db.query(BloodRequest)
        .filter(BloodRequest.status == RequestStatus.fulfilled)
        .filter(BloodRequest.fulfilled_at.isnot(None))
        .filter(BloodRequest.fulfilled_at >= start)
        .count()
    )
    return AdminOverview(
        total_donors=total_donors,
        available_now=available_now,
        active_requests=active_requests,
        fulfilled_today=fulfilled_today,
    )


@router.get("/donors", response_model=list[AdminDonorRow])
def list_donors(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AdminDonorRow]:
    _require_admin(user)
    rows = db.query(DonorProfile).order_by(DonorProfile.updated_at.desc()).all()
    today = date.today()
    out: list[AdminDonorRow] = []
    for r in rows:
        locked = r.last_donation_date is not None and (today - r.last_donation_date).days < 56
        if not r.is_available:
            status_val = "offline"
        elif locked:
            status_val = "locked"
        else:
            status_val = "available"
        out.append(
            AdminDonorRow(
                user_id=r.user_id,
                full_name=r.full_name,
                blood_group=r.blood_group,
                area_text=r.area_text,
                status=status_val,
                last_donation_date=r.last_donation_date,
            )
        )
    return out


@router.post("/donors/{donor_user_id}/suspend", response_model=dict)
def suspend_donor(
    donor_user_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _require_admin(user)
    row = db.query(DonorProfile).filter(DonorProfile.user_id == donor_user_id).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found"
        )
    row.is_available = False
    db.commit()
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="admin.donor.suspend",
        target_type="user",
        target_id=str(donor_user_id),
    )
    return {"status": "suspended"}


@router.post("/donors/{donor_user_id}/verify", response_model=dict)
def verify_donor(
    donor_user_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _require_admin(user)
    exists = db.query(DonorProfile).filter(DonorProfile.user_id == donor_user_id).first()
    if exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found"
        )
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="admin.donor.verify",
        target_type="user",
        target_id=str(donor_user_id),
    )
    return {"status": "verified"}


@router.post("/broadcast", response_model=BroadcastResponse)
def broadcast(
    body: BroadcastRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BroadcastResponse:
    _require_admin(user)
    recipients = db.query(DonorProfile).filter(DonorProfile.is_available.is_(True)).count()
    write_audit_log(
        db,
        actor_user_id=user.id,
        action="admin.broadcast",
        target_type="broadcast",
        target_id=body.target,
        meta={"message_len": len(body.message), "target": body.target},
    )
    return BroadcastResponse(recipients=recipients, target=body.target)

