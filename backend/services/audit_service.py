"""
backend/services/audit_service.py
Append-only audit log writer. No function in this module ever issues
an UPDATE or DELETE against audit_log -- only INSERT via write_audit_entry.
"""
from sqlalchemy.orm import Session

from backend.db.models import AuditLogRow


def write_audit_entry(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    actor: str,
    details: dict,
) -> None:
    row = AuditLogRow(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        details=details,
    )
    db.add(row)
    db.commit()
