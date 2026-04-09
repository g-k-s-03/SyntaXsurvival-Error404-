import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger("app.audit")


def write_audit_log(
    db: Session,
    *,
    actor_user_id: uuid.UUID | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    row = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        ip=ip,
        user_agent=(user_agent[:300] if user_agent else None),
        meta_json=json.dumps(meta, default=_json_default) if meta else None,
    )
    db.add(row)
    db.commit()
    logger.info(
        "audit action=%s actor=%s target=%s:%s ip=%s",
        action,
        actor_user_id,
        target_type,
        target_id,
        ip,
    )


def _json_default(value: Any) -> Any:
    if isinstance(value, (uuid.UUID, datetime)):
        return str(value)
    return repr(value)
