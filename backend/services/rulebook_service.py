"""
backend/services/rulebook_service.py
Reads/writes the single-row rulebook table, writing one changelog entry
per changed field (PRD Section 8.4 / 15.1).
"""
from sqlalchemy.orm import Session

from backend.db.models import RulebookChangelogRow, RulebookRow


def get_rulebook(db: Session) -> RulebookRow:
    row = db.get(RulebookRow, 1)
    if row is None:
        raise RuntimeError("Rulebook not seeded. Run scripts/seed_data.py first.")
    return row


def update_rulebook(db: Session, new_values: dict, changed_by: str) -> RulebookRow:
    row = get_rulebook(db)

    field_labels = {
        "approved_model_versions": "approved model versions",
        "minimum_confidence_threshold": "confidence threshold",
        "high_risk_conditions_requiring_review": "high-risk conditions",
    }

    for field, label in field_labels.items():
        old_value = getattr(row, field)
        new_value = new_values[field]
        if old_value != new_value:
            if field == "minimum_confidence_threshold":
                description = f"Changed {label} {old_value} -> {new_value}"
            else:
                description = f"Changed {label} from {old_value} to {new_value}"
            db.add(
                RulebookChangelogRow(changed_by=changed_by, change_description=description)
            )
        setattr(row, field, new_value)

    db.commit()
    db.refresh(row)
    return row


def get_changelog(db: Session, limit: int = 20) -> list[RulebookChangelogRow]:
    return (
        db.query(RulebookChangelogRow)
        .order_by(RulebookChangelogRow.changed_at.desc())
        .limit(limit)
        .all()
    )
