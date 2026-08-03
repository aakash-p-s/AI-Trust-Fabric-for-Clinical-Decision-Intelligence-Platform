"""
backend/routers/rulebook.py
GET/PUT /rulebook, GET /rulebook/changelog. See PRD Section 10.4.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.schemas import (
    ChangelogEntry,
    ChangelogResponse,
    ComplianceRulebook,
    ComplianceRulebookUpdate,
)
from backend.routers.deps import get_db, require_role
from backend.services import rulebook_service

router = APIRouter(prefix="/rulebook", tags=["rulebook"])


@router.get("", response_model=ComplianceRulebook)
def get_rulebook(db: Session = Depends(get_db)):
    row = rulebook_service.get_rulebook(db)
    return ComplianceRulebook(
        approved_model_versions=row.approved_model_versions,
        minimum_confidence_threshold=row.minimum_confidence_threshold,
        high_risk_conditions_requiring_review=row.high_risk_conditions_requiring_review,
    )


@router.put("")
def update_rulebook(
    payload: ComplianceRulebookUpdate,
    db: Session = Depends(get_db),
    _role: str = Depends(require_role("compliance_governance")),
):
    row = rulebook_service.update_rulebook(
        db,
        {
            "approved_model_versions": payload.approved_model_versions,
            "minimum_confidence_threshold": payload.minimum_confidence_threshold,
            "high_risk_conditions_requiring_review": payload.high_risk_conditions_requiring_review,
        },
        changed_by=payload.changed_by,
    )
    return {
        "success": True,
        "rulebook": ComplianceRulebook(
            approved_model_versions=row.approved_model_versions,
            minimum_confidence_threshold=row.minimum_confidence_threshold,
            high_risk_conditions_requiring_review=row.high_risk_conditions_requiring_review,
        ),
    }


@router.get("/changelog", response_model=ChangelogResponse)
def get_changelog(limit: int = 20, db: Session = Depends(get_db)):
    rows = rulebook_service.get_changelog(db, limit=limit)
    return ChangelogResponse(
        entries=[
            ChangelogEntry(
                changed_by=r.changed_by,
                change_description=r.change_description,
                changed_at=r.changed_at,
            )
            for r in rows
        ]
    )
